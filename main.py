import argparse
import os
import re
import requests
import time
from bs4 import BeautifulSoup as Soup
from random import randint as rnd


parser = argparse.ArgumentParser(description="Scrapes site and returns valid mega links. All links must include http(s)://")
parser.add_argument("-i", "--input", type=str, help="Input file")
parser.add_argument("-o", "--output", type=str, help="Output file")
parser.add_argument("--retry", type=int, help="Number of times to retry before continuing (default: 5)")
parser.add_argument("--no-folder", action="store_true", help="Removes folder form URL")
parser.add_argument("args", nargs=argparse.REMAINDER, help="Links to search (-i to search from file)")

args = parser.parse_args()

def isValid(url):
	id = url.split("/")[4].split("#")[0]
	if (url.split("/")[3] == "folder"):
		data = { "a": "f", "c": 1, "r": 1, "ca": 1 }
	else:
		data = { "a": "g", "p": id }

	params = {
		"id": "".join([str(rnd(0, 9)) for a in range(10)]),
		"n": id
	}

	return requests.post("https://g.api.mega.co.nz/cs", params=params, data=data).json() == -2

valid = []
toCheck = []

if args.input:
	print(f"Opening {args.input}")
	with open(args.input, "r") as f:
		toCheck = f.read().split("\n")
if args.args:
	for a in args.args:
		toCheck.append(a)

def scrape(url):
	print(f"Scraping from URL: {url}")
	for a in Soup(requests.get(url).text, "html.parser").find_all("a"):
		b = a.get("href")
		if re.compile(r"https:\/\/mega\.nz\/(file|folder)\/[\s\S]*#[\s\S]*").match(b):
			# a = a.replace("\r", "")
			print(f"Found link: {b}")
			links.append(b)
	for a in Soup(requests.get(url).text, "html.parser").get_text().split("\n"):
		if re.compile(r"https:\/\/mega\.nz\/(file|folder)\/[\s\S]*#[\s\S]*").match(a):
			a = a.replace("\r", "")
			print(f"Found link: {a}")
			links.append(a)

links = [a for a in toCheck if re.compile(r"https:\/\/mega\.nz\/(file|folder)\/[\s\S]*#[\s\S]*").match(a)]
links = list(dict.fromkeys(links))
toCheck = [a for a in toCheck if not a in links and re.compile(r"https:\/\/[\s\S]*").match(a)]

for a in toCheck:
	scrape(a)

if len(links) == 0:
	print("No links found")
	exit()

if args.no_folder:
	links = [re.match(r".{54}", a)[0] for a in links]

print(f"Checking {len(links)} links")
start = time.perf_counter()
for i, a in enumerate(l := links):
	retry = 0

	while True:
		try:
			print(f"Checking {i+1} / {len(l)}: {a}: ", end="")
			if isValid_ := isValid(a):
				valid.append(f"{a}\n")
			break
		except KeyboardInterrupt:
			print("\r")
			exit()
		except:
			retry += 1
			retryMax = args.retry if args.retry else 5
			if retry == retryMax:
				print("Failed. Skipping")
				break
			print(f"Failed. Retrying ({retry}/{retryMax})")
	try:
		print("valid" if isValid_ else "invalid")
	except:
		pass

print(f"Found {len(valid)} valid links in {round(time.perf_counter() - start)} seconds")

if args.output:
	print(f"Writing to {args.output}")
	with open(args.output, "a") as f:
		f.writelines(valid)

if (len(valid) != 0):
	while not (i := input("Would you like to open them in a new tab? [y/n]\n").lower()) in ["y", "n"]:
		print("Not a valid input")

	if (i == "y"):
		for a in valid:
			os.system(f"xdg-open {a}")