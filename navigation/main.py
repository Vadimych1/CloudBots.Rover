from src.realtimeiter import RealtimeIterator

ri = RealtimeIterator("datasets/pkl_sliced")

for d in ri:
    print(d)