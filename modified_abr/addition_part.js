// START
// tcp status variables algorithm used
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


// const expandStatus = ['tcp_sndbuf_expand','cubictcp_cong_avoid', 'tcp_try_undo_recovery', 'tcp_undo_cwnd_reduction'];
const subStatus = ['tcp_cwnd_reduction', 'tcp_xmit_recovery', 'tcp_fastretrans_alert', 'tcp_mark_skb_lost'];
let targetStatus = ['tcp_check_sack_reordering', 'tcp_xmit_recovery', 'tcp_fastretrans_alert', 'tcp_cwnd_reduction', 'tcp_try_keep_open', 'tcp_try_undo_recovery', 'tcp_try_to_open', 'cubictcp_cong_avoid', 'tcp_mark_skb_lost', 'tcp_undo_cwnd_reduction', 'tcp_sndbuf_expand',]
const MSS = 1500
let rtt = 30;
let history_reduction_interval = 0.0;
// eslint-disable-next-line no-unused-vars
const conbineSourceABR = true;
// let DashMetrics = FactoryMaker.getSingletonFactoryByName('DashMetrics');
// let DashManifestModel = FactoryMaker.getSingletonFactoryByName('DashManifestModel');


function tcpBasedInit() {
    let automaton = new Automaton();

    // 添加状态
    automaton.addState(openWindowStatus);
    automaton.addState(disorderWindowStatus);
    automaton.addState(lossWindowStatus);
    automaton.addState(recoveryWindowStatus);


    // 添加转移和条件
    automaton.addTransition(openWindowStatus, disorderWindowStatus, (event) => {
        return ['tcp_check_sack_reordering'].includes(event);
    });
    automaton.addTransition(lossWindowStatus, disorderWindowStatus, (event) => {
        return ['tcp_check_sack_reordering'].includes(event);
    });
    automaton.addTransition(recoveryWindowStatus, disorderWindowStatus, (event) => {
        return ['tcp_check_sack_reordering'].includes(event);
    });


    automaton.addTransition(openWindowStatus, recoveryWindowStatus, (event) => {
        return ['tcp_xmit_recovery', 'tcp_fastretrans_alert', 'tcp_cwnd_reduction'].includes(event);
    });
    automaton.addTransition(disorderWindowStatus, recoveryWindowStatus, (event) => {
        return ['tcp_xmit_recovery', 'tcp_fastretrans_alert', 'tcp_cwnd_reduction'].includes(event);
    });
    automaton.addTransition(lossWindowStatus, recoveryWindowStatus, (event) => {
        return [''].includes(event);
    });


    automaton.addTransition(disorderWindowStatus, openWindowStatus, (event) => {
        return ['tcp_try_keep_open', 'tcp_try_to_open', 'tcp_sndbuf_expand', 'tcp_undo_cwnd_reduction', 'cubictcp_cong_avoid'].includes(event) || event.includes('init');
    });
    automaton.addTransition(lossWindowStatus, openWindowStatus, (event) => {
        return ['tcp_try_keep_open', 'tcp_try_to_open', 'tcp_sndbuf_expand', 'tcp_undo_cwnd_reduction', 'cubictcp_cong_avoid'].includes(event) || event.includes('init');
    });
    automaton.addTransition(recoveryWindowStatus, openWindowStatus, (event) => {
        return ['tcp_try_keep_open', 'tcp_try_undo_recovery', 'tcp_try_to_open', 'cubictcp_cong_avoid', 'tcp_undo_cwnd_reduction', 'tcp_sndbuf_expand'].includes(event) || event.includes('init');
    });

    automaton.addTransition(disorderWindowStatus, lossWindowStatus, (event) => {
        return ['tcp_mark_skb_lost',].includes(event) || event.includes('lost');
    });
    automaton.addTransition(openWindowStatus, lossWindowStatus, (event) => {
        return ['tcp_mark_skb_lost',].includes(event) || event.includes('lost');
    });
    automaton.addTransition(recoveryWindowStatus, lossWindowStatus, (event) => {
        return ['tcp_mark_skb_lost',].includes(event) || event.includes('lost');
    });

    // 设置初始状态
    automaton.setCurrentState(openWindowStatus);
    TCPStatusInfo.automaton = automaton;
    // var allInput = automaton.get_all_input();
    // join all status into targetStatus
}

let usefulStatusQueue = [];
// eslint-disable-next-line no-unused-vars
let lastUsedStatusID = -1;

function findTimeDifference(subStatus, usefulStatusQueue) {
    const statusTimes = [];
    let len = statusTimes.length;

    for (let i = usefulStatusQueue.length - 1; i >= 0; i--) {
        const {msg, receivingTimestamp} = usefulStatusQueue[i];

        if (subStatus.includes(msg)) {
            statusTimes.push(receivingTimestamp);
            len = statusTimes.length;
            // if (len >= 2 && Math.abs(statusTimes[len - 1] - statusTimes[len - 2]) > 10) {
            //     break;
            // }
        }
    }

    if (len < 2) {
        return 2e9; // 返回 大数字 表示找不到足够的状态出现次数
    }

    let this_timeDifference = Math.abs(statusTimes[len - 1] - statusTimes[len - 2]);
    this_timeDifference /= 1000;
    if (history_reduction_interval <= 0) history_reduction_interval = this_timeDifference + 0.01;
    // if (this_timeDifference < 10) return history_reduction_interval
    else {
        history_reduction_interval /= 8;
        history_reduction_interval *= 7;
        history_reduction_interval += this_timeDifference / 8
    }
    history_reduction_interval=Math.max(history_reduction_interval,0.5)// 两次降窗的间隔不应低于500ms
    return history_reduction_interval // 返回时间差的绝对值
}


function calculateT(cwnd, K, w_max) {
    const t = K - Math.cbrt((w_max - cwnd));
    return t;
}

// eslint-disable-next-line no-unused-vars
function w(t, k, wmax) {
    let t_ = Math.pow((t - k), 3) + wmax;
    return t_;
}

function w_linear(t, k) {
    let t_ = k * t;
    return t_;
}

function numericalIntegration(func, lower, upper, numIntervals, k, wmax) {
    const intervalWidth = (upper - lower) / numIntervals;
    let integral = 0;

    for (let i = 0; i < numIntervals; i++) {
        const x1 = lower + i * intervalWidth;
        const x2 = x1 + intervalWidth;
        integral += (func(x1, k, wmax) + func(x2, k, wmax)) * intervalWidth / 2;
    }

    return integral;
}

// eslint-disable-next-line no-unused-vars
function getCurrentNetworkRTT(dashMetrics, type) {
    let httpRequestArray = dashMetrics.getHttpRequests(type);
    if (httpRequestArray.length === 0) {
        return null;
    }

    let lastHttpRequest = httpRequestArray[httpRequestArray.length - 1];
    if (!lastHttpRequest.trace || lastHttpRequest.trace.length === 0) {
        return null;
    }

    let lastTrace = lastHttpRequest.trace[lastHttpRequest.trace.length - 1];
    let rtt = lastTrace.s + lastTrace.d;

    return rtt;
}


function checkIfTargetStatus(status) {
    return isStatusInList(status, targetStatus);
}

function isStatusInList(lastStatus, list) {
    if (lastStatus === undefined) return false;
    for (let s1 of list) {
        if (lastStatus.msg.includes(s1)) return true;
        // if (lastStatus.includes(s1)) return true;
    }
    return false;
}

// function checkIfNeedExpand() {
//     let lastStatus = usefulStatusQueue[usefulStatusQueue.length - 1];
//     return isStatusInList(lastStatus, expandStatus);
// }
//
// function checkIfNeedSub() {
//     let lastStatus = usefulStatusQueue[usefulStatusQueue.length - 1];
//     return isStatusInList(lastStatus, subStatus);
// }

function getTCPBasedJudge(rulesContext, switchRequest) {
    const mediaInfo = rulesContext.getMediaInfo();
    const mediaType = rulesContext.getMediaType();
    if (mediaType === 'audio') {
        switchRequest.reason.withoutTCP=true
        return switchRequest;
    }
    const streamInfo = rulesContext.getStreamInfo();
    const streamId = streamInfo ? streamInfo.id : null;
    let bandwidths = [];
    const bandwithLen = mediaInfo.representationCount;
    for (let i = 0; i < bandwithLen; i += 1) {
        bandwidths.push(mediaInfo.bitrateList[i].bandwidth);
    }
    const abrController = rulesContext.getAbrController();
    const throughputHistory = abrController.getThroughputHistory();
    if(switchRequest.reason.latency===undefined) switchRequest.reason.latency=throughputHistory.getAverageLatency(mediaType)
    const latency = switchRequest.reason.latency;
    // let dashMetrics = DashMetrics(context).getInstance();
    // let dashManifest = DashManifestModel(context).getInstance();
    // rtt=dashManifest.getRoundTripTime(mediaType);

    if (TCPStatusInfo.rtt !== undefined && TCPStatusInfo.rtt > 0) {
        rtt = TCPStatusInfo.rtt;
    }
    rtt /= 1000
    // console.log('latency:'+latency);
    // console.log('rtt:'+rtt);


    // let result = switchRequest;
    // let bitrateLevel;
    // bitrateLevel = result.quality;

    let s = TCPStatusInfo.logMessages.shift();
    for (let j = 0; j < TCPStatusInfo.logMessages.length; j++) {
        if (checkIfTargetStatus(s)) {
            usefulStatusQueue.push(s)
            TCPStatusInfo.automaton.handleEvent(s.msg)
        }
        s = TCPStatusInfo.logMessages.shift();
    }

    TCPStatusInfo.logMessages.length = 0;
    // if (usefulStatusQueue.length <= 0) return switchRequest;
    let cwnd = TCPStatusInfo.curCwnd
    let W_max = TCPStatusInfo.lastMaxCwnd
    if (cwnd === undefined || W_max === undefined || cwnd <= 0 || W_max <= 0) {
        switchRequest.reason.withoutTCP=true
        return switchRequest;
    }
    switch (TCPStatusInfo.automaton.currentState) {
        case openWindowStatus:

            break;
        case disorderWindowStatus:
            break;
        case lossWindowStatus:
            cwnd *= 0.7;
            // W_max *= 0.7;
            break;
        case recoveryWindowStatus:
            cwnd *= 0.7;
            // W_max *= 0.7;
            break;
    }

    const reduction_interval = findTimeDifference(subStatus, usefulStatusQueue);
    let K = Math.min(2, reduction_interval);

    let t = 0//calculateT(cwnd, 2, W_max)

    let int_result //= numericalIntegration(w, t, K + 1.024, Math.abs(t - K) * 1000, K, W_max);

    int_result = numericalIntegration(w_linear, 0, K, Math.abs(t - K) * 1000, cwnd / rtt, W_max);
    int_result += (K) * W_max/rtt;

    let BDP = Math.abs(int_result * MSS) * 5*0.48;
    // if(rtt*1000>3*TCPStatusInfo.avg_rtt) {
    //     BDP/=3;
    //     switchRequest.reason.intoButton=true;
    // }
    const bufferLevel = dashMetrics.getCurrentBufferLevel(mediaType);
    if(bufferLevel<3){
        BDP=bandwidths[0]/2;
        switchRequest.reason.stalling=true;
    }
    const bitrate = BDP / K / 1000;//单位kb

    // let quality = abrController.getQualityForBitrate(mediaInfo, bitrate, streamId, latency);//单位kb
    // if(quality===3&&bitrate>bandwidths[bandwithLen-1]/1000) quality++;
    let quality=bandwidths.length-1;
    bandwidths[0]*=2;
    for (let i = bandwidths.length - 1; i > 0; i--) {
        if(bitrate<bandwidths[i]/1000) {
            quality=i-1;
        }
    }
    quality=0;
    for (let i = 0; i < bandwidths.length; i++) {
        if(bitrate>bandwidths[i]/1000){
            quality=i;
        }
    }
    // eslint-disable-next-line no-unused-vars
    let lastQuality = switchRequest.quality;
    console.log('BDP: ' + BDP / 1000 + ' (KB)  |  throughput: ' + switchRequest.reason.throughput + '  |  predict quality:' + quality + '  |  reduction interval: ' + reduction_interval + '  |  source quality: ' + lastQuality);


    // switchRequest.reason.throughput = bitrate;
    switchRequest.reason.cwnd = cwnd;
    switchRequest.reason.rtt = rtt;
    switchRequest.reason.State = TCPStatusInfo.automaton.currentState;
    switchRequest.priority = SwitchRequest.PRIORITY.STRONG

    // if (conbineSourceABR && lastQuality >= 10) {
    //     switchRequest.quality = Math.floor((quality + lastQuality) / 2);
    // } else {
    //     switchRequest.quality = quality;
    // }

    if ((quality > lastQuality ||bitrate>switchRequest.reason.throughput) && lastQuality <= bandwidths.length) {
        switchRequest.quality += 1;
        switchRequest.reason.change = 'UP';
        if ((quality > lastQuality + 1 ||bitrate>switchRequest.reason.throughput*2)&& lastQuality + 1 <= bandwidths.length) {
            switchRequest.quality += 1;
            switchRequest.reason.change = 'UPPER !';
            if ((quality > lastQuality + 2 ||bitrate>switchRequest.reason.throughput*4)&& lastQuality + 2 <= bandwidths.length) {
                switchRequest.quality += 1;
                switchRequest.reason.change = 'UPPER !!!';
            }
        }
    }
    else if ((quality < lastQuality - 1) && lastQuality - 1 >= 0) {
        switchRequest.quality -= 1;
        switchRequest.reason.change = 'DOWN';
        if ((quality < lastQuality - 2||bitrate<switchRequest.reason.throughput/6) && lastQuality - 2 >= 0) {
            switchRequest.quality -= 1;
            switchRequest.reason.change = 'DOWN !';
        }
    }
    // else if ((quality < lastQuality||bitrate<switchRequest.reason.throughput/1.5) && lastQuality >= 0) {
    //     switchRequest.quality -= 1;
    //     switchRequest.reason.change = 'DOWN';
    //     if ((quality < lastQuality - 1||bitrate<switchRequest.reason.throughput/3) && lastQuality - 1 >= 0) {
    //         switchRequest.quality -= 1;
    //         switchRequest.reason.change = 'DOWN !';
    //         if ((quality < lastQuality - 2||bitrate<switchRequest.reason.throughput/6) && lastQuality - 2 >= 0) {
    //             switchRequest.quality -= 1;
    //             switchRequest.reason.change = 'DOWN !!!';
    //         }
    //     }
    // }

    switchRequest.reason.source = 'calc by cubic rules using tcp status + cwnd value from server kernel';
    //
    // if (checkIfNeedExpand()) {
    //     if (lastUsedStatusID !== usefulStatusQueue[usefulStatusQueue.length - 1].messageId && bitrateLevel < bandwidths.length) {
    //         result = SwitchRequest(context).create(bitrateLevel + 1, switchRequest.reason, SwitchRequest.PRIORITY.STRONG);
    //         console.log('[tcpCheck] caused from cwnd expand signal, up the bitrate');
    //     }
    // } else if (checkIfNeedSub()) {
    //     if (bitrateLevel > 0) {
    //         result = SwitchRequest(context).create(bitrateLevel - 1, switchRequest.reason, SwitchRequest.PRIORITY.STRONG);
    //         console.log('[tcpCheck] caused from CA signal, down the bitrate');
    //     }
    // }

    if (usefulStatusQueue.length > 0) {
        // eslint-disable-next-line no-unused-vars
        lastUsedStatusID = usefulStatusQueue[usefulStatusQueue.length - 1].messageId;
    }
    return switchRequest
}

// END





// how to call it:
// switchRequest = getTCPBasedJudge(rulesContext, switchRequest);
//
// or as we used in the code:
// const tcpBasedJudgeResult = getTCPBasedJudge(rulesContext, switchRequest);
// if (mediaType!=='audio') console.log(tcpBasedJudgeResult);
// return tcpBasedJudgeResult;