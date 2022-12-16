import sqlite3 as sl
import cv2
from time import sleep
from datetime import datetime, timezone, timedelta
from string import Template
from http import HTTPStatus

boundary = "VM21grpJOSu"  # boundary for multipart/x-mixed-replace


def Content_type(x):
    dic = {"html": "text/html",
           "icon": "image/x-icon",
           "png": "image/png",
           "plain": "text/plain",
           "jpeg": "image/jpeg",
           "wav": "audio/wav",
           "replace": f"multipart/x-mixed-replace; boundary={boundary}",
           "byteranges": f"multipart/byteranges; boundary={boundary}"}
    return "Content-Type: " + dic.get(x, "text/plain")


Content_length = lambda x: f"Content-Length: {len(x)}"
Location = lambda x: f"Location: /{x}"
Status = lambda x: f"HTTP/1.1 {x} {HTTPStatus(x).phrase}"
Set_cookie = lambda x: f"Set-Cookie: " + ";".join([f"{k}={v}" for k, v in x.items()])
Content_range = lambda x, y: f"Content-Range: bytes {x}-{y}/*"
Accept_ranges = lambda x: f"Accept-Ranges: {x}"


def Get_cookie(header):
    cookie = {}
    if "Cookie" in header:
        for c in header["Cookie"].split(";"):
            k, v = c.split("=")
            cookie[k.strip()] = v.strip()
    return cookie


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


def render_membership(content, header):
    cookie = Get_cookie(header)
    if "token" not in cookie or cookie["token"] == "":
        login_information = '<h2>Please <a href="/login">login</a> to comment…</h2>'
        content = Template(content).safe_substitute(membership=login_information)
    else:
        f = open(f"pages/field/membership.html")
        form = f.read()
        f.close()
        form = Template(form).safe_substitute(value=cookie["token"])
        content = Template(content).safe_substitute(membership=form)
    return content


def add_comment(page_name, body):
    if {"user", "comment"} <= body.keys():
        db_conn = sl.connect("data.sqlite")
        c = db_conn.cursor()
        time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
        query = """
                INSERT INTO comments (post, user, comment, time)
                VALUES (?,?,?,?);
                """
        c.execute(query, (page_name, body["user"], body["comment"], time))
        db_conn.commit()
        db_conn.close()


def render_page(content, page_name, header):
    # comment list
    db_conn = sl.connect("data.sqlite")
    c = db_conn.cursor()
    c.execute(
        f"""
            SELECT * FROM comments WHERE post='{page_name}';
            """
    )
    rows = c.fetchall()
    db_conn.close()
    comment_list = ""
    for row in rows:
        comment_list += f"<li> {row[3]} -- {row[2]} ({row[4]}) </li>"
    comment_list = '<ul style="list-style-type:square">' + comment_list + '</ul>'
    content = Template(content).safe_substitute(comment_list=comment_list)

    # comment form & membership
    cookie = Get_cookie(header)
    if "token" not in cookie or cookie["token"] == "":
        login_information = '<h2>Please <a href="/login">login</a> to comment…</h2>'
        membership = '<a href="/login">Login</a>'
        content = Template(content).safe_substitute(comment_form=login_information, membership=membership)
    else:
        f = open(f"pages/field/comment_form.html")
        form = f.read()
        f.close()
        form = Template(form).safe_substitute(page_name=page_name, value=cookie["token"])
        membership = f'''Hi, {cookie["token"]}! 
        <form method="post" action="/logout/{page_name}" class="inline">
            <input type="hidden" name="useless" value="">
            <button type="submit" name="logout" value="" class="">
                Logout
            </button>
        </form>
        '''
        content = Template(content).safe_substitute(comment_form=form, membership=membership)
    return content


def login(body):
    if {"username", "password"} <= body.keys():
        db_conn = sl.connect("data.sqlite")
        c = db_conn.cursor()
        c.execute(
            f"""
                SELECT * FROM users WHERE username='{body["username"]}' AND password='{body["password"]}';
                """
        )
        rows = c.fetchall()
        db_conn.close()
        if len(rows) == 1:
            return True
        else:
            return False
    else:
        return False


def register(body):
    if {"username", "password"} <= body.keys():
        db_conn = sl.connect("data.sqlite")
        c = db_conn.cursor()
        c.execute(
            f"""
                SELECT * FROM users WHERE username='{body["username"]}';
                """
        )
        rows = c.fetchall()
        if len(rows) == 0:
            query = """
                    INSERT INTO users (username, password)
                    VALUES (?,?);
                    """
            c.execute(query, (body["username"], body["password"]))
            db_conn.commit()
            db_conn.close()
            return True
        else:
            db_conn.close()
            return False
    else:
        return False


def api(client, method, path, header, body):
    match method:
        case "GET":
            if path in ("/", "/index", "/index.html"):  # open main page
                f = open("pages/index.html")
                content = f.read()
                f.close()
                content = render_page(content, "index", header)
                response = [Status(200), Content_type("html"), Content_length(content), "", content, ""]
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)
            elif path in ("/video1", "/video2"):  # open video/audio page
                page_name = path.split("/")[1].partition("?")[0]
                f = open(f"pages/{page_name}.html")
                content = f.read()
                f.close()

                content = render_page(content, page_name, header)
                response = [Status(200), Content_type("html"), Content_length(content), "", content, ""]
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)
            elif path.startswith("/streaming/video"):  # open video streaming
                video_name = path.split("/")[2].partition("?")[0]
                print(video_name)
                if client.cap is None or not client.cap.isOpened():
                    client.cap = cv2.VideoCapture(f"./assets/{video_name}.mp4")
                if client.cap.isOpened():
                    fps = client.cap.get(cv2.CAP_PROP_FPS)
                    response = [Status(200), Content_type("replace"), "", ""]
                    response_text = "\r\n".join(response).encode()
                    client.send_response(response_text + "\r\n".encode() + video_player(client))
                    while client.signal:
                        client.send_response(video_player(client))
                        sleep(1 / fps)
                else:
                    response = [Status(403), "", ""]
                    response_text = "\r\n".join(response).encode()
                    client.send_response(response_text)
            elif path.startswith("/login"):
                f = open("pages/login.html")
                content = f.read()
                f.close()
                response = [Status(200), Content_type("html"), Content_length(content), "", content, ""]
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)
            else:
                response = [Status(404), "", ""]
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)

        case "POST":
            if path.startswith("/comment"):  # add comment
                page_name = path.split("/")[2].partition("?")[0]
                add_comment(page_name, body)
                response = [Status(303), Location(page_name), "", ""]  # redirect to video page
                print(response)
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)
            elif path.startswith("/login"):
                ret = login(body)
                if ret:
                    response = [Status(303), Location(""), Set_cookie({"token": f"{body['username']}", "path": "/"}),
                                "", ""]  # redirect to Homepage
                else:
                    content = """
                    <script>
                        alert("Wrong username or password!");
                        window.location.href = "/login";
                    </script>
                    """
                    response = [Status(401), Content_length(content), "", content, ""]

                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)
            elif path.startswith("/register"):
                ret = register(body)
                if ret:
                    print("register success")
                    response = [Status(303), Location(""), Set_cookie({"token": f"{body['username']}", "path": "/"}),
                                "", ""]
                else:
                    content = """
                    <script>
                        alert("Username already exists!");
                        window.location.href = "/login";
                    </script>
                    """
                    response = [Status(401), Content_length(content), "", content, ""]
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)

            elif path.startswith("/logout"):
                page_name = path.split("/")[2].partition("?")[0]
                print(page_name)
                response = [Status(303), Location(f"{page_name}"),
                            Set_cookie({"token": "", "path": "/", "expires": "Thu, 01 Jan 1970 00:00:00 GMT"}), "", ""]
                response_text = "\r\n".join(response).encode()
                client.send_response(response_text)
