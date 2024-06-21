import requests

url_base = "https://www.uss.co.uk"


def fetch(email, password, pin):
    """Fetch the data structure, uss_config, that contains all account information"""
    s = requests.Session()

    datasource_id = _get_login_data(s)
    _login(s, email, password, pin, datasource_id)
    uss_config = _get_uss_config(s)
    return uss_config


def extract_dc_value(uss_config):
    totalContributionsValue = float(uss_config["totalContributionsValue"][2:-2].replace(',',''))
    totalFundValue = float(uss_config["totalFundValue"][2:-2].replace(',',''))

    return {
        "totalContributionsValue": totalContributionsValue,
        "totalFundValue": totalFundValue
    }




def _get_login_data(session):
    # Get the login page to get the right cookie
    r = session.get(url_base+"/login")
    r.raise_for_status()

    for line in r.content.splitlines():
        line = line.strip()
        if line.startswith(b"\"DataSourceId\":"):
            datasource_id = line.split(b":")[1].strip()[1:-2].decode()
            break

    return datasource_id


def _login(session, email, password, pin, datasource_id):
    login_payload = {
        "email": email,
        "password": password,
        "additional":{"DataSourceId":datasource_id,"ReturnURL":""}}

    r = session.post(url_base+"/uss-api/useraccess/getpinchars", json=login_payload)
    r.raise_for_status()

    resp = r.json()
    pinRequest = resp["pinRequest"]

    pinDigitOne = int(pin[int(pinRequest["pinDigitOneLabel"][0])-1])
    pinDigitTwo = int(pin[int(pinRequest["pinDigitTwoLabel"][0])-1])
    pinDigitThree = int(pin[int(pinRequest["pinDigitThreeLabel"][0])-1])

    login_payload["pinDigitOne"] = pinDigitOne
    login_payload["pinDigitOneLabel"] = pinRequest["pinDigitOneLabel"]
    login_payload["pinDigitTwo"] = pinDigitTwo
    login_payload["pinDigitTwoLabel"] = pinRequest["pinDigitTwoLabel"]
    login_payload["pinDigitThree"] = pinDigitThree
    login_payload["pinDigitThreeLabel"] = pinRequest["pinDigitThreeLabel"]

    r = session.post(url_base+"/uss-api/useraccess/login", json=login_payload)
    r.raise_for_status()

    j = r.json()
    if not j["loginSuccess"]:
        raise Error("Login failed")


def _get_uss_config(session):
    # Must be logged in
    r = session.get(url_base+"/my-uss")
    r.raise_for_status()

    params = {}
    key_start = b"USSCONFIG."
    for line in r.content.splitlines():
        line = line.strip()
        if line.startswith(key_start):
            parts = line[len(key_start):].split(b"=")
            key = parts[0].strip().decode()
            val = parts[1].strip().decode()
            params[key] = val

    return params