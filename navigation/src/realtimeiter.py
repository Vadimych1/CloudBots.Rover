"DEPRECATED"

# import pickle as pkl
# import os
# import glob

# class RealtimeIterator(object):
#     def __init__(self, name: str) -> None:
#         self.folder = name

#     def add(self, data):
#         if not os.path.exists(self.folder):
#             os.makedirs(self.folder)
#         try:
#             pkl.dump(data, open(f"{self.folder}/{len(os.listdir(self.folder))}.pkl", "wb"))
#         except:
#             print("Error writing to file (in iterator.add)")

#     def delete(self):
#         for path in glob.glob(f"{self.folder}/*.pkl"):
#             os.remove(path)

#     def __iter__(self):
#         for f in glob.glob(f"{self.folder}/*.pkl"):
#             for d in pkl.load(open(f, "rb")):
#                 yield d

#     def __len__(self):
#         lens = 0
#         for f in glob.glob(f"{self.folder}/*.pkl"):
#             lens += len(pkl.load(open(f, "rb")))
#         return lens