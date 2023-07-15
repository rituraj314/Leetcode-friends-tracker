import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template,request
import sqlite3
from datetime import datetime
import lxml

app = Flask(__name__)

conn = sqlite3.connect("usernames.sqlite")
cursor = conn.cursor()
sql_query = """CREATE TABLE IF NOT EXISTS username (
   userid TEXT NOT NULL
)"""

cursor.execute(sql_query)
conn.commit()

def db_connection():
    conn = None
    try:
        conn = sqlite3.connect("usernames.sqlite")
    except sqlite3.error as e:
        print(e)
    return conn

def scrape_leetcode_profile(username):
    # Construct the URL based on the provided username
    url = f"https://leetcode.com/{username}"

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "lxml")

        # Extract information from the parsed HTML
        name = soup.find("div", class_="text-label-1 dark:text-dark-label-1 break-all text-base font-semibold").text.strip()
    
        questionSolved = soup.find_all("span",class_="mr-[5px] text-base font-medium leading-[20px] text-label-1 dark:text-dark-label-1")

        easySolved = questionSolved[0].text.strip()
        mediumSolved = questionSolved[1].text.strip()
        hardSolved = questionSolved[2].text.strip()
        
        constestRating = soup.find("div",class_="text-label-1 dark:text-dark-label-1 flex items-center text-2xl").text.strip();

        recentACs = soup.find_all("span",class_="text-label-1 dark:text-dark-label-1 font-medium line-clamp-1",limit= 5)

        links_light = soup.find_all('a', class_= "flex h-[56px] items-center rounded px-4 bg-fill-4 dark:bg-dark-fill-4",limit = 5)
        
        links_dark = soup.find_all('a',class_="flex h-[56px] items-center rounded px-4",limit=5)

        time = soup.find_all("span",class_="text-label-3 dark:text-dark-label-3 hidden whitespace-nowrap lc-md:inline",limit=5)
        
        attended = soup.find_all("div",class_="text-label-1 dark:text-dark-label-1 font-medium leading-[22px]");
        
        ranking = soup.find("span",class_="ttext-label-1 dark:text-dark-label-1 font-medium").text.strip();
        
        

        href_links = [0]*5
        prefix = "https://leetcode.com"
       
        href_links[0] = prefix + links_light[0]['href']
        href_links[1] = prefix + links_dark[0]['href']
        href_links[2] = prefix + links_light[1]['href']
        href_links[3] = prefix + links_dark[1]['href']
        href_links[4] = prefix + links_light[2]['href']
        
        current_time = datetime.now().strftime('%H:%M:%S %Y-%m-%d ')
        

        profile_data = {
            "Name": name,
            "EasySolved": easySolved,
            "MediumSolved": mediumSolved,
            "HardSolved": hardSolved,
            "CurrentContestRating": constestRating,
            "ContestAttended": attended[1].text.strip(),
            "Rank":ranking,
            "RecentfiveAC":[recentACs[i].text.strip() for i in range(5)],
            "Time": [time[i].text.strip() for i in range(5)],
            "Links": href_links,
            "lastUpdatedAt" : current_time
            

        }
        return profile_data

    else:
        return 404
    


Dict = {}

@app.route("/",methods = ['GET','POST','PUT'])
def index():
    conn = db_connection()
    cursor = conn.cursor()


    if request.method == 'GET':
        cursor = conn.execute("SELECT * FROM username")
        users = [
            dict(username = row[0])
            for row in cursor.fetchall()
        ]
        if users is not None:
            for i in range(len(users)):
                if Dict.get(users[i]['username']) == None:
                    profileData = scrape_leetcode_profile(users[i]['username'])
                    if(profileData != 404):
                        Dict[users[i]['username']] = profileData


    errormsg = ""

    if request.method == 'POST':
        user = request.form['username']
        method = request.form['_method']
        
        if len(user) == 0:
            errormsg = "Username Can't be empty!"
            return render_template('index.html',Dict = Dict,error = errormsg)
        
        if method == 'PUT':
            Dict[user] = scrape_leetcode_profile(user)
            return render_template('index.html',Dict = Dict)
            
        if method == 'DELETE':
            del Dict[user]
            query = "DELETE FROM username WHERE userid = ?"
            cursor.execute(query, (user,))
            conn.commit()
            return render_template('index.html',Dict = Dict)
            
        if Dict.get(user) == None:
                    profileData = scrape_leetcode_profile(user)
                    if(profileData != 404):
                        Dict[user] = profileData
                    
                    else:
                        errormsg = "User Doesn't Exist! or an error occured."

                    sql = """INSERT INTO username (userid)
                                SELECT ?
                                WHERE NOT EXISTS (
                                    SELECT 1 FROM username WHERE userid = ?
                                );"""
                                
                    cursor.execute(sql,(user,user))
                    conn.commit()
                    
        
        else:
            errormsg = "Username Already Exist!"
                       

    return render_template('index.html',Dict = Dict,error = errormsg)

if __name__ == '__main__':
    app.run(debug=True)
