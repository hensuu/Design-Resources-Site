import sys
import sqlite3 as sl
import cv2
from time import sleep
from datetime import datetime, timezone, timedelta
from string import Template

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
Location = lambda x: f"Location:/{x}"
Status_200 = "HTTP/1.1 200 OK"
Status_303 = "HTTP/1.1 303 See Other"
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


def add_comment(path, body):
    if {"user", "comment"} <= body.keys():
        db_conn = sl.connect("data.sqlite")
        c = db_conn.cursor()
        time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
        query = """
                INSERT INTO comments (post, user, comment, time)
                VALUES (?,?,?,?);
                """
        c.execute(query, (path, body["user"], body["comment"], time))
        db_conn.commit()


def render_comment_list(content, path):
    db_conn = sl.connect("data.sqlite")
    c = db_conn.cursor()
    c.execute(
        f"""
        SELECT * FROM comments WHERE post='{path}';
        """
    )
    rows = c.fetchall()
    comments = []
    for row in rows:
        comments.append(f"{row[3]} -- {row[2]} ({row[4]})")
    comment_list = "".join(["<li>" + x + "</li>" for x in comments])
    template = Template(content)
    rendered_content = template.substitute(comments=comment_list)

    return rendered_content


def api(client, method, path, body):
    match method:
        case "GET":
            if path in ("/", "/index.html"):  # open main page
                f = open("pages/index.html")
                content = f.read()
                f.close()
                response = [Status_200, Content_type("html"), Content_length(content), "", content, ""]
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)
            elif path in ("/video1", "/video2"):
                page_name = path.split("/")[1].partition("?")[0]
                f = open(f"pages/{page_name}.html")
                content = f.read()
                f.close()
                content = render_comment_list(content, page_name)
                response = [Status_200, Content_type("html"), Content_length(content), "", content, ""]
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)
            elif path.startswith("/streaming"):
                video_name = path.split("/")[2].partition("?")[0]
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
            else:
                response = [Status_404, "", ""]
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)

        case "POST":
            if path.startswith("/comment"):
                page_name = path.split("/")[2].partition("?")[0]
                add_comment(page_name, body)
                response = [Status_303, Location(page_name), "", ""]
                print(response)
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)
