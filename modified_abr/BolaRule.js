/* eslint-disable no-undef */
/* eslint-disable no-unused-vars */
/**
 * The copyright in this software is being made available under the BSD License,
 * included below. This software may be subject to other third party and contributor
 * rights, including patent rights, and no such rights are granted under this license.
 *
 * Copyright (c) 2016, Dash Industry Forum.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *  * Redistributions of source code must retain the above copyright notice, this
 *  list of conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright notice,
 *  this list of conditions and the following disclaimer in the documentation and/or
 *  other materials provided with the distribution.
 *  * Neither the name of Dash Industry Forum nor the names of its
 *  contributors may be used to endorse or promote products derived from this software
 *  without specific prior written permission.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY
 *  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 *  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 *  IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
 *  INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
 *  NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 *  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 *  WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 *  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 *  POSSIBILITY OF SUCH DAMAGE.
 */

// For a description of the BOLA adaptive bitrate (ABR) algorithm, see http://arxiv.org/abs/1601.06748

import MetricsConstants from '../../constants/MetricsConstants';
import SwitchRequest from '../SwitchRequest';
import FactoryMaker from '../../../core/FactoryMaker';
import {HTTPRequest} from '../../vo/metrics/HTTPRequest';
import EventBus from '../../../core/EventBus';
import Events from '../../../core/events/Events';
import Debug from '../../../core/Debug';
import MediaPlayerEvents from '../../MediaPlayerEvents';
import Constants from '../../constants/Constants';

// BOLA_STATE_ONE_BITRATE   : If there is only one bitrate (or initialization failed), always return NO_CHANGE.
// BOLA_STATE_STARTUP       : Set placeholder buffer such that we download fragments at most recently measured throughput.
// BOLA_STATE_STEADY        : Buffer primed, we switch to steady operation.
// TODO: add BOLA_STATE_SEEK and tune BOLA behavior on seeking
const BOLA_STATE_ONE_BITRATE = 0;
const BOLA_STATE_STARTUP = 1;
const BOLA_STATE_STEADY = 2;

const MINIMUM_BUFFER_S = 10; // BOLA should never add artificial delays if buffer is less than MINIMUM_BUFFER_S.
const MINIMUM_BUFFER_PER_BITRATE_LEVEL_S = 2;
// E.g. if there are 5 bitrates, BOLA switches to top bitrate at buffer = 10 + 5 * 2 = 20s.
// If Schedule Controller does not allow buffer to reach that level, it can be achieved through the placeholder buffer level.

const PLACEHOLDER_BUFFER_DECAY = 0.99; // Make sure placeholder buffer does not stick around too long.

function BolaRule(config) {
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


    config = config || {};
    const context = this.context;

    const dashMetrics = config.dashMetrics;
    const mediaPlayerModel = config.mediaPlayerModel;
    const eventBus = EventBus(context).getInstance();

    let instance,
        logger,
        bolaStateDict;

    function setup() {
        tcpBasedInit();
        logger = Debug(context).getInstance().getLogger(instance);
        resetInitialSettings();

        eventBus.on(MediaPlayerEvents.BUFFER_EMPTY, onBufferEmpty, instance);
        eventBus.on(MediaPlayerEvents.PLAYBACK_SEEKING, onPlaybackSeeking, instance);
        eventBus.on(MediaPlayerEvents.METRIC_ADDED, onMetricAdded, instance);
        eventBus.on(MediaPlayerEvents.QUALITY_CHANGE_REQUESTED, onQualityChangeRequested, instance);
        eventBus.on(MediaPlayerEvents.FRAGMENT_LOADING_ABANDONED, onFragmentLoadingAbandoned, instance);

        eventBus.on(Events.MEDIA_FRAGMENT_LOADED, onMediaFragmentLoaded, instance);
    }

    function utilitiesFromBitrates(bitrates) {
        return bitrates.map(b => Math.log(b));
        // no need to worry about offset, utilities will be offset (uniformly) anyway later
    }

    // NOTE: in live streaming, the real buffer level can drop below minimumBufferS, but bola should not stick to lowest bitrate by using a placeholder buffer level
    function calculateBolaParameters(stableBufferTime, bitrates, utilities) {
        const highestUtilityIndex = utilities.reduce((highestIndex, u, uIndex) => (u > utilities[highestIndex] ? uIndex : highestIndex), 0);

        if (highestUtilityIndex === 0) {
            // if highestUtilityIndex === 0, then always use lowest bitrate
            return null;
        }

        const bufferTime = Math.max(stableBufferTime, MINIMUM_BUFFER_S + MINIMUM_BUFFER_PER_BITRATE_LEVEL_S * bitrates.length);

        // TODO: Investigate if following can be better if utilities are not the default Math.log utilities.
        // If using Math.log utilities, we can choose Vp and gp to always prefer bitrates[0] at minimumBufferS and bitrates[max] at bufferTarget.
        // (Vp * (utility + gp) - bufferLevel) / bitrate has the maxima described when:
        // Vp * (utilities[0] + gp - 1) === minimumBufferS and Vp * (utilities[max] + gp - 1) === bufferTarget
        // giving:
        const gp = (utilities[highestUtilityIndex] - 1) / (bufferTime / MINIMUM_BUFFER_S - 1);
        const Vp = MINIMUM_BUFFER_S / gp;
        // note that expressions for gp and Vp assume utilities[0] === 1, which is true because of normalization

        return { gp: gp, Vp: Vp };
    }

    function getInitialBolaState(rulesContext) {
        const initialState = {};
        const mediaInfo = rulesContext.getMediaInfo();
        const bitrates = mediaInfo.bitrateList.map(b => b.bandwidth);
        let utilities = utilitiesFromBitrates(bitrates);
        utilities = utilities.map(u => u - utilities[0] + 1); // normalize
        const stableBufferTime = mediaPlayerModel.getStableBufferTime();
        const params = calculateBolaParameters(stableBufferTime, bitrates, utilities);

        if (!params) {
            // only happens when there is only one bitrate level
            initialState.state = BOLA_STATE_ONE_BITRATE;
        } else {
            initialState.state = BOLA_STATE_STARTUP;

            initialState.bitrates = bitrates;
            initialState.utilities = utilities;
            initialState.stableBufferTime = stableBufferTime;
            initialState.Vp = params.Vp;
            initialState.gp = params.gp;

            initialState.lastQuality = 0;
            clearBolaStateOnSeek(initialState);
        }

        return initialState;
    }

    function clearBolaStateOnSeek(bolaState) {
        bolaState.placeholderBuffer = 0;
        bolaState.mostAdvancedSegmentStart = NaN;
        bolaState.lastSegmentWasReplacement = false;
        bolaState.lastSegmentStart = NaN;
        bolaState.lastSegmentDurationS = NaN;
        bolaState.lastSegmentRequestTimeMs = NaN;
        bolaState.lastSegmentFinishTimeMs = NaN;
    }

    // If the buffer target is changed (can this happen mid-stream?), then adjust BOLA parameters accordingly.
    function checkBolaStateStableBufferTime(bolaState, mediaType) {
        const stableBufferTime = mediaPlayerModel.getStableBufferTime();
        if (bolaState.stableBufferTime !== stableBufferTime) {
            const params = calculateBolaParameters(stableBufferTime, bolaState.bitrates, bolaState.utilities);
            if (params.Vp !== bolaState.Vp || params.gp !== bolaState.gp) {
                // correct placeholder buffer using two criteria:
                // 1. do not change effective buffer level at effectiveBufferLevel === MINIMUM_BUFFER_S ( === Vp * gp )
                // 2. scale placeholder buffer by Vp subject to offset indicated in 1.

                const bufferLevel = dashMetrics.getCurrentBufferLevel(mediaType);
                let effectiveBufferLevel = bufferLevel + bolaState.placeholderBuffer;

                effectiveBufferLevel -= MINIMUM_BUFFER_S;
                effectiveBufferLevel *= params.Vp / bolaState.Vp;
                effectiveBufferLevel += MINIMUM_BUFFER_S;

                bolaState.stableBufferTime = stableBufferTime;
                bolaState.Vp = params.Vp;
                bolaState.gp = params.gp;
                bolaState.placeholderBuffer = Math.max(0, effectiveBufferLevel - bufferLevel);
            }
        }
    }

    function getBolaState(rulesContext) {
        const mediaType = rulesContext.getMediaType();
        let bolaState = bolaStateDict[mediaType];
        if (!bolaState) {
            bolaState = getInitialBolaState(rulesContext);
            bolaStateDict[mediaType] = bolaState;
        } else if (bolaState.state !== BOLA_STATE_ONE_BITRATE) {
            checkBolaStateStableBufferTime(bolaState, mediaType);
        }
        return bolaState;
    }

    // The core idea of BOLA.
    function getQualityFromBufferLevel(bolaState, bufferLevel) {
        const bitrateCount = bolaState.bitrates.length;
        let quality = NaN;
        let score = NaN;
        for (let i = 0; i < bitrateCount; ++i) {
            let s = (bolaState.Vp * (bolaState.utilities[i] + bolaState.gp) - bufferLevel) / bolaState.bitrates[i];
            if (isNaN(score) || s >= score) {
                score = s;
                quality = i;
            }
        }
        return quality;
    }

    // maximum buffer level which prefers to download at quality rather than wait
    function maxBufferLevelForQuality(bolaState, quality) {
        return bolaState.Vp * (bolaState.utilities[quality] + bolaState.gp);
    }

    // the minimum buffer level that would cause BOLA to choose quality rather than a lower bitrate
    function minBufferLevelForQuality(bolaState, quality) {
        const qBitrate = bolaState.bitrates[quality];
        const qUtility = bolaState.utilities[quality];

        let min = 0;
        for (let i = quality - 1; i >= 0; --i) {
            // for each bitrate less than bitrates[quality], BOLA should prefer quality (unless other bitrate has higher utility)
            if (bolaState.utilities[i] < bolaState.utilities[quality]) {
                const iBitrate = bolaState.bitrates[i];
                const iUtility = bolaState.utilities[i];

                const level = bolaState.Vp * (bolaState.gp + (qBitrate * iUtility - iBitrate * qUtility) / (qBitrate - iBitrate));
                min = Math.max(min, level); // we want min to be small but at least level(i) for all i
            }
        }
        return min;
    }

    /*
     * The placeholder buffer increases the effective buffer that is used to calculate the bitrate.
     * There are two main reasons we might want to increase the placeholder buffer:
     *
     * 1. When a segment finishes downloading, we would expect to get a call on getMaxIndex() regarding the quality for
     *    the next segment. However, there might be a delay before the next call. E.g. when streaming live content, the
     *    next segment might not be available yet. If the call to getMaxIndex() does happens after a delay, we don't
     *    want the delay to change the BOLA decision - we only want to factor download time to decide on bitrate level.
     *
     * 2. It is possible to get a call to getMaxIndex() without having a segment download. The buffer target in dash.js
     *    is different for top-quality segments and lower-quality segments. If getMaxIndex() returns a lower-than-top
     *    quality, then the buffer controller might decide not to download a segment. When dash.js is ready for the next
     *    segment, getMaxIndex() will be called again. We don't want this extra delay to factor in the bitrate decision.
     */
    function updatePlaceholderBuffer(bolaState, mediaType) {
        const nowMs = Date.now();

        if (!isNaN(bolaState.lastSegmentFinishTimeMs)) {
            // compensate for non-bandwidth-derived delays, e.g., live streaming availability, buffer controller
            const delay = 0.001 * (nowMs - bolaState.lastSegmentFinishTimeMs);
            bolaState.placeholderBuffer += Math.max(0, delay);
        } else if (!isNaN(bolaState.lastCallTimeMs)) {
            // no download after last call, compensate for delay between calls
            const delay = 0.001 * (nowMs - bolaState.lastCallTimeMs);
            bolaState.placeholderBuffer += Math.max(0, delay);
        }

        bolaState.lastCallTimeMs = nowMs;
        bolaState.lastSegmentStart = NaN;
        bolaState.lastSegmentRequestTimeMs = NaN;
        bolaState.lastSegmentFinishTimeMs = NaN;

        checkBolaStateStableBufferTime(bolaState, mediaType);
    }

    function onBufferEmpty(e) {
        // if we rebuffer, we don't want the placeholder buffer to artificially raise BOLA quality
        const mediaType = e.mediaType;
        // if audio buffer runs empty (due to track switch for example) then reset placeholder buffer only for audio (to avoid decrease video BOLA quality)
        const stateDict = mediaType === Constants.AUDIO ? [Constants.AUDIO] : bolaStateDict;
        for (const mediaType in stateDict) {
            if (bolaStateDict.hasOwnProperty(mediaType) && bolaStateDict[mediaType].state === BOLA_STATE_STEADY) {
                bolaStateDict[mediaType].placeholderBuffer = 0;
            }
        }
    }

    function onPlaybackSeeking() {
        // TODO: 1. Verify what happens if we seek mid-fragment.
        // TODO: 2. If e.g. we have 10s fragments and seek, we might want to download the first fragment at a lower quality to restart playback quickly.
        for (const mediaType in bolaStateDict) {
            if (bolaStateDict.hasOwnProperty(mediaType)) {
                const bolaState = bolaStateDict[mediaType];
                if (bolaState.state !== BOLA_STATE_ONE_BITRATE) {
                    bolaState.state = BOLA_STATE_STARTUP; // TODO: BOLA_STATE_SEEK?
                    clearBolaStateOnSeek(bolaState);
                }
            }
        }
    }

    function onMediaFragmentLoaded(e) {
        if (e && e.chunk && e.chunk.mediaInfo) {
            const bolaState = bolaStateDict[e.chunk.mediaInfo.type];
            if (bolaState && bolaState.state !== BOLA_STATE_ONE_BITRATE) {
                const start = e.chunk.start;
                if (isNaN(bolaState.mostAdvancedSegmentStart) || start > bolaState.mostAdvancedSegmentStart) {
                    bolaState.mostAdvancedSegmentStart = start;
                    bolaState.lastSegmentWasReplacement = false;
                } else {
                    bolaState.lastSegmentWasReplacement = true;
                }

                bolaState.lastSegmentStart = start;
                bolaState.lastSegmentDurationS = e.chunk.duration;
                bolaState.lastQuality = e.chunk.quality;

                checkNewSegment(bolaState, e.chunk.mediaInfo.type);
            }
        }
    }

    function onMetricAdded(e) {
        if (e && e.metric === MetricsConstants.HTTP_REQUEST && e.value && e.value.type === HTTPRequest.MEDIA_SEGMENT_TYPE && e.value.trace && e.value.trace.length) {
            const bolaState = bolaStateDict[e.mediaType];
            if (bolaState && bolaState.state !== BOLA_STATE_ONE_BITRATE) {
                bolaState.lastSegmentRequestTimeMs = e.value.trequest.getTime();
                bolaState.lastSegmentFinishTimeMs = e.value._tfinish.getTime();

                checkNewSegment(bolaState, e.mediaType);
            }
        }
    }

    /*
     * When a new segment is downloaded, we get two notifications: onMediaFragmentLoaded() and onMetricAdded(). It is
     * possible that the quality for the downloaded segment was lower (not higher) than the quality indicated by BOLA.
     * This might happen because of other rules such as the DroppedFramesRule. When this happens, we trim the
     * placeholder buffer to make BOLA more stable. This mechanism also avoids inflating the buffer when BOLA itself
     * decides not to increase the quality to avoid oscillations.
     *
     * We should also check for replacement segments (fast switching). In this case, a segment is downloaded but does
     * not grow the actual buffer. Fast switching might cause the buffer to deplete, causing BOLA to drop the bitrate.
     * We avoid this by growing the placeholder buffer.
     */
    function checkNewSegment(bolaState, mediaType) {
        if (!isNaN(bolaState.lastSegmentStart) && !isNaN(bolaState.lastSegmentRequestTimeMs) && !isNaN(bolaState.placeholderBuffer)) {
            bolaState.placeholderBuffer *= PLACEHOLDER_BUFFER_DECAY;

            // Find what maximum buffer corresponding to last segment was, and ensure placeholder is not relatively larger.
            if (!isNaN(bolaState.lastSegmentFinishTimeMs)) {
                const bufferLevel = dashMetrics.getCurrentBufferLevel(mediaType);
                const bufferAtLastSegmentRequest = bufferLevel + 0.001 * (bolaState.lastSegmentFinishTimeMs - bolaState.lastSegmentRequestTimeMs); // estimate
                const maxEffectiveBufferForLastSegment = maxBufferLevelForQuality(bolaState, bolaState.lastQuality);
                const maxPlaceholderBuffer = Math.max(0, maxEffectiveBufferForLastSegment - bufferAtLastSegmentRequest);
                bolaState.placeholderBuffer = Math.min(maxPlaceholderBuffer, bolaState.placeholderBuffer);
            }

            // then see if we should grow placeholder buffer

            if (bolaState.lastSegmentWasReplacement && !isNaN(bolaState.lastSegmentDurationS)) {
                // compensate for segments that were downloaded but did not grow the buffer
                bolaState.placeholderBuffer += bolaState.lastSegmentDurationS;
            }

            bolaState.lastSegmentStart = NaN;
            bolaState.lastSegmentRequestTimeMs = NaN;
        }
    }

    function onQualityChangeRequested(e) {
        // Useful to store change requests when abandoning a download.
        if (e) {
            const bolaState = bolaStateDict[e.mediaType];
            if (bolaState && bolaState.state !== BOLA_STATE_ONE_BITRATE) {
                bolaState.abrQuality = e.newQuality;
            }
        }
    }

    function onFragmentLoadingAbandoned(e) {
        if (e) {
            const bolaState = bolaStateDict[e.mediaType];
            if (bolaState && bolaState.state !== BOLA_STATE_ONE_BITRATE) {
                // deflate placeholderBuffer - note that we want to be conservative when abandoning
                const bufferLevel = dashMetrics.getCurrentBufferLevel(e.mediaType);
                let wantEffectiveBufferLevel;
                if (bolaState.abrQuality > 0) {
                    // deflate to point where BOLA just chooses newQuality over newQuality-1
                    wantEffectiveBufferLevel = minBufferLevelForQuality(bolaState, bolaState.abrQuality);
                } else {
                    wantEffectiveBufferLevel = MINIMUM_BUFFER_S;
                }
                const maxPlaceholderBuffer = Math.max(0, wantEffectiveBufferLevel - bufferLevel);
                bolaState.placeholderBuffer = Math.min(bolaState.placeholderBuffer, maxPlaceholderBuffer);
            }
        }
    }

    function getMaxIndex(rulesContext) {
        const switchRequest = SwitchRequest(context).create();

        if (!rulesContext || !rulesContext.hasOwnProperty('getMediaInfo') || !rulesContext.hasOwnProperty('getMediaType') ||
            !rulesContext.hasOwnProperty('getScheduleController') || !rulesContext.hasOwnProperty('getStreamInfo') ||
            !rulesContext.hasOwnProperty('getAbrController') || !rulesContext.hasOwnProperty('useBufferOccupancyABR')) {
            return switchRequest;
        }
        const mediaInfo = rulesContext.getMediaInfo();
        const mediaType = rulesContext.getMediaType();
        const scheduleController = rulesContext.getScheduleController();
        const streamInfo = rulesContext.getStreamInfo();
        const abrController = rulesContext.getAbrController();
        const throughputHistory = abrController.getThroughputHistory();
        const streamId = streamInfo ? streamInfo.id : null;
        const isDynamic = streamInfo && streamInfo.manifestInfo && streamInfo.manifestInfo.isDynamic;
        const useBufferOccupancyABR = rulesContext.useBufferOccupancyABR();
        switchRequest.reason = switchRequest.reason || {};

        if (!useBufferOccupancyABR) {
            return switchRequest;
        }

        scheduleController.setTimeToLoadDelay(0);

        const bolaState = getBolaState(rulesContext);

        if (bolaState.state === BOLA_STATE_ONE_BITRATE) {
            // shouldn't even have been called
            return switchRequest;
        }

        const bufferLevel = dashMetrics.getCurrentBufferLevel(mediaType);
        const throughput = throughputHistory.getAverageThroughput(mediaType, isDynamic);
        const safeThroughput = throughputHistory.getSafeAverageThroughput(mediaType, isDynamic);
        const latency = throughputHistory.getAverageLatency(mediaType);
        let quality;

        switchRequest.reason.state = bolaState.state;
        switchRequest.reason.throughput = throughput;
        switchRequest.reason.latency = latency;

        if (isNaN(throughput)) { // isNaN(throughput) === isNaN(safeThroughput) === isNaN(latency)
            // still starting up - not enough information
            return switchRequest;
        }

        switch (bolaState.state) {
            case BOLA_STATE_STARTUP:
                quality = abrController.getQualityForBitrate(mediaInfo, safeThroughput, streamId, latency);

                switchRequest.quality = quality;
                switchRequest.reason.throughput = safeThroughput;

                bolaState.placeholderBuffer = Math.max(0, minBufferLevelForQuality(bolaState, quality) - bufferLevel);
                bolaState.lastQuality = quality;

                if (!isNaN(bolaState.lastSegmentDurationS) && bufferLevel >= bolaState.lastSegmentDurationS) {
                    bolaState.state = BOLA_STATE_STEADY;
                }

                break; // BOLA_STATE_STARTUP

            case BOLA_STATE_STEADY:

                // NB: The placeholder buffer is added to bufferLevel to come up with a bitrate.
                //     This might lead BOLA to be too optimistic and to choose a bitrate that would lead to rebuffering -
                //     if the real buffer bufferLevel runs out, the placeholder buffer cannot prevent rebuffering.
                //     However, the InsufficientBufferRule takes care of this scenario.

                updatePlaceholderBuffer(bolaState, mediaType);

                quality = getQualityFromBufferLevel(bolaState, bufferLevel + bolaState.placeholderBuffer);

                // we want to avoid oscillations
                // We implement the "BOLA-O" variant: when network bandwidth lies between two encoded bitrate levels, stick to the lowest level.
                const qualityForThroughput = abrController.getQualityForBitrate(mediaInfo, safeThroughput, streamId, latency);
                if (quality > bolaState.lastQuality && quality > qualityForThroughput) {
                    // only intervene if we are trying to *increase* quality to an *unsustainable* level
                    // we are only avoid oscillations - do not drop below last quality

                    quality = Math.max(qualityForThroughput, bolaState.lastQuality);
                }

                // We do not want to overfill buffer with low quality chunks.
                // Note that there will be no delay if buffer level is below MINIMUM_BUFFER_S, probably even with some margin higher than MINIMUM_BUFFER_S.
                let delayS = Math.max(0, bufferLevel + bolaState.placeholderBuffer - maxBufferLevelForQuality(bolaState, quality));

                // First reduce placeholder buffer, then tell schedule controller to pause.
                if (delayS <= bolaState.placeholderBuffer) {
                    bolaState.placeholderBuffer -= delayS;
                    delayS = 0;
                } else {
                    delayS -= bolaState.placeholderBuffer;
                    bolaState.placeholderBuffer = 0;

                    if (quality < abrController.getMaxAllowedIndexFor(mediaType, streamId)) {
                        // At top quality, allow schedule controller to decide how far to fill buffer.
                        scheduleController.setTimeToLoadDelay(1000 * delayS);
                    } else {
                        delayS = 0;
                    }
                }

                switchRequest.quality = quality;
                switchRequest.reason.throughput = throughput;
                switchRequest.reason.latency = latency;
                switchRequest.reason.bufferLevel = bufferLevel;
                switchRequest.reason.placeholderBuffer = bolaState.placeholderBuffer;
                switchRequest.reason.delay = delayS;

                bolaState.lastQuality = quality;
                // keep bolaState.state === BOLA_STATE_STEADY

                break; // BOLA_STATE_STEADY

            default:
                logger.debug('BOLA ABR rule invoked in bad state.');
                // should not arrive here, try to recover
                switchRequest.quality = abrController.getQualityForBitrate(mediaInfo, safeThroughput, streamId, latency);
                switchRequest.reason.state = bolaState.state;
                switchRequest.reason.throughput = safeThroughput;
                switchRequest.reason.latency = latency;
                bolaState.state = BOLA_STATE_STARTUP;
                clearBolaStateOnSeek(bolaState);
        }

        const tcpBasedJudgeResult = getTCPBasedJudge(rulesContext, switchRequest,global);
        console.log(tcpBasedJudgeResult);
        return tcpBasedJudgeResult;

        // return switchRequest;
    }

    function resetInitialSettings() {
        bolaStateDict = {};
    }

    function reset() {
        resetInitialSettings();

        eventBus.off(MediaPlayerEvents.BUFFER_EMPTY, onBufferEmpty, instance);
        eventBus.off(MediaPlayerEvents.PLAYBACK_SEEKING, onPlaybackSeeking, instance);
        eventBus.off(MediaPlayerEvents.METRIC_ADDED, onMetricAdded, instance);
        eventBus.off(MediaPlayerEvents.QUALITY_CHANGE_REQUESTED, onQualityChangeRequested, instance);
        eventBus.off(MediaPlayerEvents.FRAGMENT_LOADING_ABANDONED, onFragmentLoadingAbandoned, instance);

        eventBus.off(Events.MEDIA_FRAGMENT_LOADED, onMediaFragmentLoaded, instance);
    }

    instance = {
        getMaxIndex: getMaxIndex,
        reset: reset
    };

    setup();
    return instance;
}

BolaRule.__dashjs_factory_name = 'BolaRule';
export default FactoryMaker.getClassFactory(BolaRule);
