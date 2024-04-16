//get nginx pid
const {isIPv4, isIPv6} = require('net');
const os = require('os-utils');
const fs = require('fs');
const WebSocket = require('ws');
const {exec, spawn} = require("child_process");


const too_many_status = {
    "cubictcp_cwnd_event": -1,
    "tcp_parse_md5sig_option": -1,
    "tcp_rcv_established": -1,
    "tcp_queue_rcv": -1,
    "tcp_event_data_recv": -1,
    "tcp_data_ready": -1,
    "__tcp_ack_snd_check": -1,
    "tcp_rcv_space_adjust": -1,
    "tcp_rbtree_insert": -1,
    "tcp_rearm_rto": -1,
    "tcp_check_space": -1,
    "tcp_try_coalesce": -1,
    "tcp_ack": -1,
    "tcp_ack_tstamp": -1,
    "cubictcp_acked": -1,
    "tcp_urg": -1,
    "tcp_data_queue": -1,
    "tcp_try_rmem_schedule": -1,
    "tcp_parse_options": -1

}
// 定义全局变量用于记录数据量
let originalDataSize = 0;
let totalDataSize = 0;


function getNginxPid() {
    const {exec} = require('child_process');

// 获取 Nginx 主进程的 PID 并存储在全局变量中
    exec("ps aux | grep 'apache2' | grep -v grep | awk '{print $2}'", (error, stdout, stderr) => {
        if (error) {
            console.error(`执行命令时发生错误：${error.message}`);
            return;
        }
        if (stderr) {
            console.error(`命令执行产生了错误输出：${stderr}`);
            return;
        }

// 提取 Nginx 进程的 PID，以空格分割为数组
        let nginxPids = stdout.trim().split(/\s+/);
        console.log(`Nginx 所有进程的 PID 是：${nginxPids}`);

        // 存储 PID 到全局变量中
        global.nginxPids = nginxPids;
    });
    return global.nginxPids
}

getNginxPid();

function runStap() {
//systemtap
    const {spawn} = require('child_process');
    const cmd = 'sudo'; // 运行的外部命令
    const find = spawn(cmd, ['/home/cc/systemtap-4.9/stap', '/home/cc/systemtap-test/socket-trace.stp']);

//const find = exec(cmd);
    find.stdout.setEncoding('utf8');
    const readline = require('readline');


// 监听子进程的关闭事件
    find.on('close', (code) => {
        console.log(`子进程退出，退出码 ${code}`);
    });
    find.on('error', (error) => {
        console.error('子进程出现错误：', error);
    });
    return {find, readline};
}

const {find, readline} = runStap();

//ws
const server = new WebSocket.Server({port: 3000});
let handler = monitorCpuUsageToFile('cpu.csv', 100);

server.on('connection', (socket, request) => {
    let lastCwnd=0;
    let lastCwndTime=0
    let clientIP = request.connection.remoteAddress;

    // Check if the IP address is IPv6
    if (isIPv6(clientIP)) {
        // Extract the IPv4 address from the IPv6 address
        clientIP = clientIP.replace(/^.*:/, '');
    }
    clientIP = clientIP.trim();
    let messageCounter = 0; // 用于编号消息
    console.log('Client connected IP:', clientIP);

    originalDataSize = 0;
    totalDataSize = 0;

    // filename = "serverMessage.txt"
    // fs.writeFile(filename, "START RECORD\n", (err) => {
    //     if (err) throw err;
    // });

    // 创建逐行读取接口
    const rl = readline.createInterface({
        input: find.stdout
    });
    // 监听每一行输出
    rl.on('line', (line) => {
        const kind_part = line.substring(0, line.indexOf("->"));

        if (kind_part.includes("input") || kind_part.includes("cubic")) {
            // line = line.substring(line.indexOf(' ') + 1);
            for (const pid of global.nginxPids) {
                if (kind_part.includes(pid)) {
                    const timestamp = new Date().getTime();
                    line = line.substring(line.indexOf("->") + 2).trim();
                    if (line in too_many_status) {
                        return;
                    }
                    // 构造消息对象
                    const messageId = ++messageCounter;
                    const serverMessage = {
                        type: 'tcp_func_call', data: {
                            messageId, timestamp, message: line
                        }
                    };
                    // 将消息发送给客户端
                    let serverMessageStr = JSON.stringify(serverMessage);
                    originalDataSize += serverMessageStr.length;
                    const tcpHeaderSize = 20; // 假设 TCP 包头大小为 20 字节
                    totalDataSize += serverMessageStr.length + tcpHeaderSize;

                    socket.send(serverMessageStr);
                    break;
                }
            }
        }
        else if (kind_part.includes("cwnd")) {
            line = line.substring(line.indexOf("->") + 2).trim();
            const timestamp = new Date().getTime();
            if(Math.abs(timestamp-lastCwndTime)<10) return;
            else lastCwndTime=timestamp;

            // 提取 IP 地址
            const ipRegex = /ip: \[(\d+\.\d+\.\d+\.\d+)\]/;
            const ipMatch = line.match(ipRegex);
            const ipAddress = ipMatch ? ipMatch[1] : "IP_FAILED";
            if (ipAddress !== clientIP) {
                return;
            }

            // 提取时间戳
            const timestampRegex = /\[(\d+)\]/;
            const timestampMatch = line.match(timestampRegex);
            const timestampValue = timestampMatch ? parseInt(timestampMatch[1]) * 1000 : timestamp;

            // 提取 cur_cwnd
            const curCwndRegex = /cur_cwnd: \[(\d+)\]/;
            const curCwndMatch = line.match(curCwndRegex);
            const curCwnd = curCwndMatch ? parseInt(curCwndMatch[1]) : -1;

            if(lastCwnd===curCwnd) return;
            else lastCwnd=curCwnd;

            // 提取 last_max_cwnd
            const lastMaxCwndRegex = /last_max_cwnd: \[(\d+)\]/;
            const lastMaxCwndMatch = line.match(lastMaxCwndRegex);
            const lastMaxCwnd = lastMaxCwndMatch ? parseInt(lastMaxCwndMatch[1]) : -1;

            // 提取 ssthresh
            const ssthreshRegex = /ssthresh: \[(\d+)\]/;
            const ssthreshMatch = line.match(ssthreshRegex);
            const ssthresh = ssthreshMatch ? parseInt(ssthreshMatch[1]) : -1;

            // 提取 rtt
            const rttRegex = /rtt: \[(\d+)\]/;
            const rttMatch = line.match(rttRegex);
            const rtt = rttMatch ? parseInt(rttMatch[1]) : -1;

            // check if any var is -1
            if (curCwnd === -1 || lastMaxCwnd === -1 || ssthresh === -1 || rtt === -1) {
                return;
            }
            const messageId = ++messageCounter;

            const serverMessage = {//時間戳以stap輸出為準
                type: 'cwnd_change', data: {
                    messageId, timestamp: timestampValue, curCwnd, lastMaxCwnd, ssthresh, rtt
                }
            };
            socket.send(JSON.stringify(serverMessage));
        } else if (kind_part.includes("ca_state")) {
            // line = line.substring(line.indexOf(' ') + 1).trim();
            for (const pid of global.nginxPids) {
                if (kind_part.includes(pid)) {
                    // console.log(line);
                    const messageId = ++messageCounter;
                    const timestamp = new Date().getTime();
                    line = line.substring(line.indexOf("->") + 2).trim();

                    // 提取 ca_state 字段值
                    const caStateRegex = /ca_state=0x(\w+)/;
                    const caStateMatch = line.match(caStateRegex);
                    const caStateValue = caStateMatch ? parseInt(caStateMatch[1], 16) : -1;
                    if (caStateValue === -1) return;

                    // 提取最后的时间戳数字
                    const timestampRegex = /\[(\d+)\]/;
                    const timestampMatch = line.match(timestampRegex);
                    const timestampValue = timestampMatch ? parseInt(timestampMatch[1]) : timestamp;

                    const serverMessage = {//時間戳以stap輸出為準
                        type: 'ca_state_change', data: {
                            messageId, timestamp: timestampValue, caState: caStateValue
                        }
                    };
                    // console.log(serverMessage)

                    socket.send(JSON.stringify(serverMessage));
                    break;
                }
            }
        }

    });

    // 监听客户端发来的消息
    socket.on('message', (data) => {
        const clientMessage = JSON.parse(data);

        if (clientMessage.type === 'clientResponse') {
            // 处理客户端的回应消息
            const messageId = clientMessage.data.messageId;
            const clientTimestamp = clientMessage.data.sendingTimestamp;

            // 计算往返时延
            const roundTripTime = new Date().getTime() - clientTimestamp;

            // 打印日志
            //console.log(`Received client response for message ${messageId}: Round-trip time: ${roundTripTime} ms`);
            const feedbackMessage = {
                type: 'feedback', data: {
                    messageId, roundTripTime
                }
            };
            socket.send(JSON.stringify(feedbackMessage));
        } else if (clientMessage.type === 'clockSync') {
            const messageId = clientMessage.messageId;
            const serverTimestamp = new Date().getTime();
            const clientTimestamp = clientMessage.clientTimestamp;

            const clockSyncRespMessage = {
                type: 'clockSyncResp', data: {
                    messageId, serverTimestamp, clientTimestamp
                }
            };
            socket.send(JSON.stringify(clockSyncRespMessage));
        } else {
            // 处理其他类型的消息
            console.log(`Received from client: ${data}`);
        }
    });
    // 当客户端断开连接时停止发送消息
    socket.on('close', () => {
        // clearInterval(handler);
        console.log('Client disconnected');
    });
});


function monitorCpuUsageToFile(filePath, interval = 500) {
    const csvHeader = 'Timestamp,CPU_Usage,Original_Data_Size,Total_Data_Size\n';

    // 写入表头到指定文件
    fs.writeFile(filePath, csvHeader, (err) => {
        if (err) {
            console.error('无法写入表头到文件:', err);
        } else {
            console.log(`已创建 ${filePath} 文件并写入表头`);
        }
    });

    function monitorCpuUsage() {
        os.cpuUsage((usage) => {
            const timestamp = new Date().getTime();

            // 构造记录的数据行
            const dataRow = `${timestamp},${(usage * 100).toFixed(2)},${originalDataSize},${totalDataSize}\n`;

            fs.appendFile(filePath, dataRow, (err) => {
                if (err) {
                    console.error('无法写入到文件:', err);
                }
            });
        });
    }

    // 每隔指定时间间隔输出一次 CPU 利用率和数据量到指定文件
    let handler = setInterval(monitorCpuUsage, interval);
    return handler;
}