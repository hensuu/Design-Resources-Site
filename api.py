import sys

import cv2
from time import sleep

boundary = "VM21grpJOSu"


def Content_type(x):
    dic = {"html": "text/html",
           "icon": "image/x-icon",
           "png": "image/png",
           "plain": "text/plain",
           "jpeg": "image/jpeg",
           "multipart": f"multipart/x-mixed-replace; boundary={boundary}"}
    return "Content-Type:" + dic.get(x, "text/plain")


Content_length = lambda x: f"Content-Length:{len(x)}"

Status_200 = "HTTP/1.1 200 OK"
Status_404 = "HTTP/1.1 404 Not Found"
Connections = "Connections:close"


def video_player(client):
    ret, frame = client.cap.read()
    if ret:
        frame = cv2.imencode('.jpg', frame)[1].tobytes()
        response = [f"--{boundary}", Content_type("jpeg"), "", ""]
        response_text = "\r\n".join(response).encode()
        response_text += frame
        response_text += "\r\n".encode()
        return response_text
    else:
        client.kill()


def api(method, path, client):
    match method:
        case "GET":
            if path.startswith("/favicon.ico"):
                response = [Status_404, "", ""]
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)
            elif path=="/":  # open main page
                f = open("pages/index.html")
                content = f.read()
                f.close()
                response = [Status_200, Content_type("html"), Content_length(content), "", content, ""]
                response_text = "\r\n".join(response).encode()
                client.send_response( response_text)
            elif path.startswith(("/video1.html", "/video2.html")):
                f = open(f"pages{path}")
                content = f.read()
                f.close()
                response = [Status_200, Content_type("html"), Content_length(content), "", content, ""]
                response_text = "\r\n".join(response).encode()
                client.send_response( response_text)
            elif path.startswith("/streaming"):
                video_name=path.split("/")[2]
                print(video_name)
                if client.cap is None or not client.cap.isOpened():
                    client.cap = cv2.VideoCapture(f"./assets/{video_name}.mp4")
                if client.cap.isOpened():
                    fps = client.cap.get(cv2.CAP_PROP_FPS)
                    response = [Status_200, Content_type("multipart"), "", ""]
                    response_text = "\r\n".join(response).encode()
                    client.send_response(response_text + "\r\n".encode() + video_player(client))
                    while client.signal:
                        client.send_response(video_player(client))
                        sleep(1 / fps)
                else:
                    response = [Status_404, "", ""]
                    response_text = "\r\n".join(response).encode()
                    client.send_response(response_text)




