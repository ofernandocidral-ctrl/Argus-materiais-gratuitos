import sys
import numpy as np
N=33
x=np.linspace(0,1,N)
def scurve(v,k=0.18):
    return v+k*(v-0.5)*(1-np.abs(2*v-1))*1.0  # gentle S, keeps endpoints
lines=["TITLE \"soft_clean\"",f"LUT_3D_SIZE {N}"]
for b in x:
  for g in x:
    for r in x:
      c=np.array([r,g,b])
      c=0.015+c*0.975          # lift blacks slightly
      c=scurve(c)
      l=0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
      c=l+(c-l)*1.06           # +6% saturation
      c=c*np.array([1.008,1.0,0.985])  # subtle warmth
      c=np.clip(c,0,1)
      lines.append("%.6f %.6f %.6f"%tuple(c))
open(sys.argv[1] if len(sys.argv)>1 else "soft_clean.cube","w").write("\n".join(lines)+"\n")
