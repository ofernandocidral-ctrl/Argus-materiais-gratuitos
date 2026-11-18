import os, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else "sfx"
os.makedirs(OUT, exist_ok=True)
import numpy as np, wave
SR=48000
def save(name,x):
    x=x/ (np.max(np.abs(x))+1e-9)*0.8
    d=(np.clip(x,-1,1)*32767).astype(np.int16)
    st=np.stack([d,d],1).reshape(-1)
    w=wave.open(os.path.join(OUT, f"{name}.wav"),"wb");w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(st.tobytes());w.close()
rng=np.random.default_rng(1)
def lp(x,a):  # one-pole lowpass with time-varying alpha
    y=np.zeros_like(x);p=0
    for i in range(len(x)):
        p+=a[i]*(x[i]-p);y[i]=p
    return y
# whoosh: noise through sweeping lowpass, bell envelope
n=int(SR*0.45);t=np.linspace(0,1,n)
a=0.02+0.35*np.sin(np.pi*t)**2
x=lp(rng.standard_normal(n),a)-lp(rng.standard_normal(n),a*0.15)
save("whoosh",x*np.sin(np.pi*t)**1.5)
# pop: short pitched blip
n=int(SR*0.09);t=np.arange(n)/SR
f=900*np.exp(-t*25)+300
save("pop",np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*45))
# ding: soft bell
n=int(SR*0.9);t=np.arange(n)/SR
save("ding",(np.sin(2*np.pi*1318*t)+0.5*np.sin(2*np.pi*2637*t)+0.25*np.sin(2*np.pi*3951*t))*np.exp(-t*5)*(1-np.exp(-t*400)))
# click: tick for text
n=int(SR*0.03);t=np.arange(n)/SR
save("click",rng.standard_normal(n)*np.exp(-t*300)+np.sin(2*np.pi*2400*t)*np.exp(-t*200))
# riser
n=int(SR*1.2);t=np.linspace(0,1,n)
a=0.01+0.5*t**2
save("riser",lp(rng.standard_normal(n),a)*t**2+0.3*np.sin(2*np.pi*np.cumsum(200+800*t**2)/SR)*t**3)
# hit: impacto grave para número de abertura e palavras-chave (aprovado na abertura exemplo)
n=int(SR*0.8);t=np.arange(n)/SR
save("hit",0.9*np.sin(2*np.pi*np.cumsum(42+90*np.exp(-18*t))/SR)*np.exp(-5*t)+0.25*rng.standard_normal(n)*np.exp(-40*t))
