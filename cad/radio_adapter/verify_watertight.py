import struct
import collections
import sys
import os

def check_stl_watertight(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} does not exist.")
        return False
        
    with open(filepath, 'rb') as f:
        header = f.read(80)
        num_triangles = struct.unpack('<I', f.read(4))[0]
        
        edges = collections.defaultdict(int)
        min_p = [float('inf'), float('inf'), float('inf')]
        max_p = [float('-inf'), float('-inf'), float('-inf')]
        
        for _ in range(num_triangles):
            data = f.read(50)
            floats = struct.unpack('<12fH', data)
            v1, v2, v3 = floats[3:6], floats[6:9], floats[9:12]
            
            for v in (v1, v2, v3):
                for ax in range(3):
                    min_p[ax] = min(min_p[ax], v[ax])
                    max_p[ax] = max(max_p[ax], v[ax])
                    
            def q(p):
                return (round(p[0], 3), round(p[1], 3), round(p[2], 3))
                
            q1, q2, q3 = q(v1), q(v2), q(v3)
            edges[(q1, q2)] += 1
            edges[(q2, q3)] += 1
            edges[(q3, q1)] += 1
            
    unmatched = 0
    for (p1, p2), cnt in edges.items():
        opp_cnt = edges.get((p2, p1), 0)
        if cnt != opp_cnt:
            unmatched += abs(cnt - opp_cnt)
            
    basename = os.path.basename(filepath)
    print(f"[{basename}]")
    print(f"  Triangles: {num_triangles}")
    print(f"  Bounds X:  {min_p[0]:7.2f} to {max_p[0]:7.2f} (size: {max_p[0]-min_p[0]:6.2f} mm)")
    print(f"  Bounds Y:  {min_p[1]:7.2f} to {max_p[1]:7.2f} (size: {max_p[1]-min_p[1]:6.2f} mm)")
    print(f"  Bounds Z:  {min_p[2]:7.2f} to {max_p[2]:7.2f} (size: {max_p[2]-min_p[2]:6.2f} mm)")
    print(f"  Watertight (unmatched edges): {unmatched} {'[PASS - 100% Watertight]' if unmatched == 0 else '[FAIL]'}")
    return unmatched == 0

if __name__ == '__main__':
    stls = sys.argv[1:]
    if not stls:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        stls = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith('.stl') and not f.startswith('focus_radio_frame')]
    
    all_ok = True
    for s in stls:
        if not check_stl_watertight(s):
            all_ok = False
        print("-" * 50)
    sys.exit(0 if all_ok else 1)
