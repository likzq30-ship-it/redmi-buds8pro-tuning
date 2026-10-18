import json, math, sys

# 由 baseline(实测) + harman(目标) + 本文件内的 boost 定义 生成 MXGA 拟合目标
# 用法: python3 build_target.py baseline.json harman.json out.json
#   baseline.json: [[freq, dB], ...]  (Buds 8 Pro 实测, 957 点)
#   harman.json  : [[freq, dB], ...]  (哈曼 in-ear 2024 Beta 5128, 72 点)

def interp(rows, f):
    if f <= rows[0][0]: return rows[0][1]
    if f >= rows[-1][0]: return rows[-1][1]
    lo, hi = 0, len(rows) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if rows[mid][0] <= f: lo = mid
        else: hi = mid
    f0, d0 = rows[lo]; f1, d1 = rows[hi]
    t = (math.log(f) - math.log(f0)) / (math.log(f1) - math.log(f0)) if f1 > f0 else 0
    return d0 + (d1 - d0) * t

def bell(f, gain, fc, width_oct):
    return gain * math.exp(-((math.log2(f / fc) / width_oct) ** 2))

# 华语抒情-人声版 的 boost 定义
def boost(f):
    return (bell(f,  3.5,   75, 1.0)    # 底鼓/贝斯体感
          + bell(f, -1.5,  250, 0.9)    # 去糊
          + bell(f,  2.5, 1200, 0.9)    # 男声胸腔/靠前
          + bell(f,  2.0, 2800, 0.9)    # 咬字清晰
          + bell(f, -1.8, 6500, 0.7)    # 齿音压制
          + bell(f,  2.0, 11000, 0.8))  # 空气感

def main(base_path, harm_path, out_path):
    base = json.load(open(base_path))
    harm = json.load(open(harm_path))
    base_n = [(f, v - (interp(base, 500) - 60)) for f, v in base]
    harm_n = [(f, v - (interp(harm, 500) - 60)) for f, v in harm]
    out = []
    for f, v in harm_n:
        if f <= 12000:
            val = v
        elif f >= 15000:
            val = interp(base_n, f)          # 15k 以上跟随耳机自身滚降
        else:
            t = (math.log(f) - math.log(12000)) / (math.log(15000) - math.log(12000))
            val = v + (interp(base_n, f) - v) * t
        out.append([round(f, 3), round(val + boost(f), 3)])
    off = interp(out, 500) - 60.0
    out = [[f, round(v - off, 3)] for f, v in out]
    json.dump(out, open(out_path, 'w'))
    print('wrote', out_path, len(out), 'points')

if __name__ == '__main__':
    main(*sys.argv[1:4])
