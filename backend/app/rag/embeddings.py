import hashlib, math

def embed(text: str, dim: int = 384):
    vec=[0.0]*dim
    for token in text.lower().split():
        h=int(hashlib.sha256(token.encode()).hexdigest(),16)
        vec[h%dim]+=1.0
    norm=math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v/norm for v in vec]

def cosine(a,b): return sum(x*y for x,y in zip(a,b))
