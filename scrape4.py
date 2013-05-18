import json
from functools import partial
import requests
from bs4 import BeautifulSoup

URL = "http://coverage.celcom.com.my/CelcomCoverageIIPub/faces/CelcomCoverage.jsp"
def open_page():
	r = requests.get(URL)
	soup = BeautifulSoup(r.text)
	return r.cookies, soup.select("input#javax.faces.ViewState")[0]["value"]

PAYLOAD = {
	"form1:bttnNext": "Submit >>",
	"form1:ddlState": None,
	"form1:txtArea": '',
	"form1:txtBuilding": None,
	"form1:txtStreet": '',
	"form1_hidden": "form1_hidden",
	"javax.faces.ViewState": None,
}
def query_celcom(cookies, view_state, state, area):
	state = state.replace("W.P.", "WP")
	payload = PAYLOAD.copy()
	payload["form1:ddlState"] = state
	payload["form1:txtBuilding"] = area
	payload["javax.faces.ViewState"] = view_state

	r = requests.post(URL, cookies=cookies, data=payload)
	return r.text

def get_results(content):
	soup = BeautifulSoup(content)
	msg = soup.select("#form1:stxtMessage")
	if msg and msg[0].text.startswith("No record"):
		texts = []
	else:
		texts = [opt.text for opt in soup.select("option")]
	print texts
	return texts

print "load data..."
data = json.load(open("data/pru13_demographics.json"))
print "open query page..."
cookies, view_state = open_page()

for s in data:
	print "state: " + s

	query = partial(query_celcom, cookies, view_state, s)
	pcs = data[s]["parliament_constituencies"]

	for pc in pcs:
		obj = pcs[pc]

		if "3G_penetration" in obj:
			continue

		print "parliament_constituency: " + obj["name"]

		cname = obj["name"].lower()
		for suffix in ("utara", "selatan", "timor", "barat"):
			cname = cname.replace(' ' + suffix, '')
		print "simpler name: " + cname

		scs = obj["state_constituencies"]
		names = [cname] + [sobj["name"].lower() for sobj in scs.values()]

		print "all names: " + str(names)

		try:
			obj["3G_penetration"] = sum(map(len, map(get_results, map(query, names))))
		except:
			pass

print "save data..."
with open("pru13_demographics.json", 'w') as f:
	json.dump(data, f)
