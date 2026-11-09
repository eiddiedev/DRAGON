// 用法：swift render_stem.swift <score.json> <输出目录>
// 用系统 GM 音色库离线渲染每个声部为独立 wav。score: {tracks:[{name,program,bank?,notes:[[start,dur,midi,vel],...]}], length}
import AVFoundation
import Foundation
let args = CommandLine.arguments
let data = try! Data(contentsOf: URL(fileURLWithPath: args[1]))
let score = try! JSONSerialization.jsonObject(with: data) as! [String: Any]
let tracks = score["tracks"] as! [[String: Any]]
let length = (score["length"] as! NSNumber).doubleValue
let dls = URL(fileURLWithPath: "/System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls")
let sr = 44100.0
for t in tracks {
    let name = t["name"] as! String
    let program = (t["program"] as! NSNumber).uint8Value
    let isDrum = (t["drum"] as? NSNumber)?.boolValue ?? false
    let notes = t["notes"] as! [[NSNumber]]
    let engine = AVAudioEngine()
    let sampler = AVAudioUnitSampler()
    engine.attach(sampler)
    engine.connect(sampler, to: engine.mainMixerNode, format: nil)
    let format = AVAudioFormat(standardFormatWithSampleRate: sr, channels: 2)!
    try! engine.enableManualRenderingMode(.offline, format: format, maximumFrameCount: 4096)
    try! sampler.loadSoundBankInstrument(at: dls, program: program, bankMSB: UInt8(isDrum ? 0x78 : 0x79), bankLSB: 0)
    try! engine.start()
    let total = AVAudioFramePosition((length + 6) * sr)
    // 事件按时间排序
    var events: [(Int64, Bool, UInt8, UInt8)] = []
    for n in notes {
        let st = Int64(n[0].doubleValue * sr), en = Int64((n[0].doubleValue + n[1].doubleValue) * sr)
        events.append((st, true, n[2].uint8Value, n[3].uint8Value))
        events.append((en, false, n[2].uint8Value, 0))
    }
    events.sort { $0.0 < $1.0 }
    let url = URL(fileURLWithPath: args[2]).appendingPathComponent(name + ".wav")
    let file = try! AVAudioFile(forWriting: url, settings: format.settings)
    let buf = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: 1024)!
    var pos: Int64 = 0
    var ei = 0
    while pos < total {
        while ei < events.count && events[ei].0 <= pos {
            let e = events[ei]
            if e.1 { sampler.startNote(e.2, withVelocity: e.3, onChannel: 0) } else { sampler.stopNote(e.2, onChannel: 0) }
            ei += 1
        }
        let st = try! engine.renderOffline(1024, to: buf)
        if st == .success { try! file.write(from: buf) }
        pos += 1024
    }
    engine.stop()
    print("rendered", name)
}
