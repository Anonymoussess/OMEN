let TCPStatusInfo = {};
// WebSocket connection code
const socket = new WebSocket('ws://dash.nginx.show:3000');
const hash = new Map()
TCPStatusInfo.logMessages=[];
TCPStatusInfo.rttCount=0;
TCPStatusInfo.avg_rtt=0;
// global.usefulStatusQueue=[];
let clockOffset = 0;
// castate=0
const openWindowStatus = 'open_window';
//1      (2 is cwr)
const disorderWindowStatus = 'disorder_window';
//3
const recoveryWindowStatus = 'recovery_window';
//4
const lossWindowStatus = 'loss_window';
class Automaton {
    constructor() {
        this.currentState = null; // 当前状态
        this.transitions = new Map(); // 转移规则
        this.states = new Set(); // 所有状态集合
    }

    // 添加状态
    addState(state) {
        this.states.add(state);
    }

    // 添加转移和条件
    addTransition(fromState, toState, condition) {
        if (!this.states.has(fromState) || !this.states.has(toState)) {
            throw new Error('Invalid state');
        }

        if (!this.transitions.has(fromState)) {
            this.transitions.set(fromState, []);
        }

        this.transitions.get(fromState).push({toState: toState, condition: condition});
    }

    get_all_input() {
        //write a func return all the toState in transitions
        let all_input = new Set();
        for (const [key, value] of this.transitions) {
            for (const transition of value) {
                all_input.add(transition.toState);
            }
            all_input.add(key);
        }
        //return the list forum
        return all_input;
    }

    // 设置当前状态
    setCurrentState(state) {
        this.currentState = state;
    }

    // 处理事件
    handleEvent(event) {
        if (!this.currentState) {
            throw new Error('Current state is not set');
        }

        const transitions = this.transitions.get(this.currentState);
        if (!transitions) {
            throw new Error('No transitions defined for current state');
        }

        for (const transition of transitions) {
            if (transition.condition(event)) { // 根据条件判断是否满足转移条件
                this.currentState = transition.toState; // 更新当前状态
                return;
            }
        }

        // throw new Error('No matching transition found for event');
    }

}

socket.onopen = () => {
    console.log('WebSocket 连接成功');

    // 循环发送消息进行时钟同步
    let AllNumSyncs = 10; // 设置要进行的同步次数

    let outInterval = setInterval(() => {
        let numSyncs = 10; // 设置要进行的同步次数
        let intervalId = setInterval(() => {
            const timestamp = Date.now(); // 获取当前时间戳
            const message = JSON.stringify({
                messageId: numSyncs, type: 'clockSync', clientTimestamp: timestamp
            });

            // 发送消息到服务器
            socket.send(message);
            numSyncs--;
            if (numSyncs <= 0) {
                clearInterval(intervalId);
            }
        }, 100);
        AllNumSyncs--;
        if (AllNumSyncs <= 0) {
            clearInterval(outInterval);
        }
    },1000);
};

function addLogMessage(messageId, transferTime, receivingTimestamp, msg) {
    let status={
        messageId: messageId,
        transferTime: transferTime,
        receivingTimestamp: receivingTimestamp,
        msg: msg
    };
    TCPStatusInfo.logMessages.push(status);
}

socket.addEventListener('message', (event) => {
    const serverMessage = JSON.parse(event.data);
    if (serverMessage.type === 'tcp_func_call') {
        const sendingTimestamp = serverMessage.data.timestamp;
        const messageId = serverMessage.data.messageId;
        const msg = serverMessage.data.message;

        const receivingTimestamp = new Date().getTime();
        const transferTime = receivingTimestamp - clockOffset - sendingTimestamp;

        console.log(`Received message ${messageId} | type: ${serverMessage.type} | Happened at: ${receivingTimestamp} | Content is : ${msg}`);
        addLogMessage(messageId, transferTime, receivingTimestamp, msg.trim());
    }
    else if (serverMessage.type === 'cwnd_change') {
        const timestamp = serverMessage.data.timestamp;
        const messageId = serverMessage.data.messageId;
        const curCwnd = serverMessage.data.curCwnd;
        const lastMaxCwnd = serverMessage.data.lastMaxCwnd;
        const ssthresh = serverMessage.data.ssthresh;
        const rtt = serverMessage.data.rtt/8;

        // if cur cwnd<之前的lastMax，那麼last=cur*0.85。如果cur>之前的last，那麼現在的last=cur
        // ssthresh=cur*0.7
        TCPStatusInfo.curCwnd=curCwnd;
        TCPStatusInfo.lastMaxCwnd=lastMaxCwnd;
        TCPStatusInfo.rtt=rtt;

        TCPStatusInfo.rttCount++;
        TCPStatusInfo.avg_rtt=TCPStatusInfo.avg_rtt*(TCPStatusInfo.rttCount-1)/TCPStatusInfo.rttCount+
            (rtt/TCPStatusInfo.rttCount);

        console.log(`Received message ${messageId} | type: ${serverMessage.type} | Happened at: ${timestamp} | Content is : curCwnd: ${curCwnd}, lastMaxCwnd: ${lastMaxCwnd}, rtt: ${rtt}`);
        //todo update
    }
    else if (serverMessage.type === 'ca_state_change') {
        const timestamp = serverMessage.data.timestamp;
        const messageId = serverMessage.data.messageId;
        const caStateValue = serverMessage.data.caState;
        if(caStateValue.includes("0x0")){
            TCPStatusInfo.automaton.setCurrentState(openWindowStatus);
        }else if(caStateValue.includes("0x1")){
            TCPStatusInfo.automaton.setCurrentState(disorderWindowStatus);
        }else if(caStateValue.includes("0x3")){
            TCPStatusInfo.automaton.setCurrentState(recoveryWindowStatus);
        }else if(caStateValue.includes("0x4")){
            TCPStatusInfo.automaton.setCurrentState(lossWindowStatus);
        }

        console.log(`Received message ${messageId} | type: ${serverMessage.type} | Happened at: ${timestamp} | Content is : ${caStateValue}`);
        //todo update
    }
    else if (serverMessage.type === 'feedback') {
        const messageId = serverMessage.data.messageId;
        const rtt = serverMessage.data.roundTripTime;

        console.log(`Received message ${messageId}| RTT : ${rtt} | ${hash.get(messageId)} `);
    }
    else if (serverMessage.type === 'clockSyncResp') {
        const messageId = serverMessage.data.messageId;
        const serverTimestamp = serverMessage.data.serverTimestamp; // 服务器返回的时间戳
        const clientTimestamp = serverMessage.data.clientTimestamp;
        const roundTripTime = new Date().getTime() - clientTimestamp;

        // const transTime = serverTimestamp - clientTimestamp;
        const realTransTime = roundTripTime / 2;
        // const offset = transTime - realTransTime;
        const offset = clientTimestamp + realTransTime - serverTimestamp

        console.log(`${messageId} times clock sync offset is  ${offset} ms`);
        // ,rtt is ${roundTripTime}, client send at ${clientTimestamp}, server rcv at ${serverTimestamp}`);

        // 最后一次同步完成后计算平均值并输出
        if (clockOffset === 0) {
            clockOffset = offset;
        } else {
            clockOffset = (clockOffset * 7 / 8) + (offset / 8);
            console.log(`clock offset avg value change to ${clockOffset} ms`);
        }
    }
});

// // Send a message to the server
// const messageToSend = 'Hello from client!';
// socket.send(messageToSend);
