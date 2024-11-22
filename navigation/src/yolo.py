import yolov5 as y

def load_model(path: str):
    return y.load(path)

def predict(img, model):
    results = model(img)

    classes = results.names
    for result in results.xyxy[0]:
        # print(result)
        result = result.tolist()
        d = classes[result[-1]]