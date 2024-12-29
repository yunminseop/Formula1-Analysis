from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

matplotlib.use("TkAgg")

remote = mysql.connector.connect(
    host = "****",
    port = "3306",
    user = "root",
    password = "****",
    database = "F1_Analysis"
)

cur = remote.cursor()

year_list = ["2019", "2020", "2021", "2022", "2023", "2024"]

constructor_in_total = {}
for year in year_list:
    url = "https://www.formula1.com/en/results/"+year+"/races"
    page = urlopen(url)

    soup = BeautifulSoup(page, "html.parser")
    
    race_total = soup.find_all("ul")[5]

    a_list = race_total.find_all(class_="block")

    race_result = []
    fastest_laps = []

    url_in_each_year = []

    for idx, a in enumerate(a_list):
        each_record = []
        race_result_url = a["href"]
        fastest_lap_url = str(a["href"]).replace("race-result", "fastest-laps")
        each_record.append("https://www.formula1.com/"+race_result_url)
        each_record.append("https://www.formula1.com/"+fastest_lap_url)
        url_in_each_year.append(each_record)

    url_in_each_year= url_in_each_year[1:]
    # print(url_in_each_year)


    constructor_in_each_year = {}

    for idx, urls in enumerate(url_in_each_year):
        
        url_race_result = urls[0].replace("'","")
        url_fastest_lap = urls[1].replace("'","")
        

        response_rr = requests.get(url_race_result)
        response_rr.raise_for_status()

        response_fl = requests.get(url_fastest_lap)
        response_fl.raise_for_status()

        
        soup_2019_rr = BeautifulSoup(response_rr.text, "html.parser")
        soup_2019_fl = BeautifulSoup(response_fl.text, "html.parser")
        
        find_fl_tbody = soup_2019_fl.find_all("tbody")
        try:
            find_fl_class = find_fl_tbody[0].find_all(class_="bg-brand-white")

            find_fl_info = find_fl_class[0].find_all(class_="f1-text font-titillium tracking-normal font-normal non-italic normal-case leading-none f1-text__micro text-fs-15px")

            fl_driver_name = find_fl_info[2].get_text()[:-3]
            fl_constructor = find_fl_info[3].get_text()
            
            if fl_constructor in constructor_in_each_year:
                constructor_in_each_year[fl_constructor] += 1
            else:
                constructor_in_each_year[fl_constructor] = 1

            find_rr_tbody = soup_2019_rr.find_all("tbody")

            find_rr_class_odd = find_rr_tbody[0].find_all(class_="bg-brand-white")
            find_rr_class_even = find_rr_tbody[0].find_all(class_="bg-grey-10")
            
            for idx_odd, each in enumerate(find_rr_class_odd):
                info = each.find_all(class_="f1-text font-titillium tracking-normal font-normal non-italic normal-case leading-none f1-text__micro text-fs-15px")
                if info[2].get_text()[:-3] == fl_driver_name:
                    fl_driver_rank = 2*(idx_odd+1)-1
            
            for idx_even, each in enumerate(find_rr_class_even):
                info = each.find_all(class_="f1-text font-titillium tracking-normal font-normal non-italic normal-case leading-none f1-text__micro text-fs-15px")
                if info[2].get_text()[:-3] == fl_driver_name:
                    fl_driver_rank = 2*(idx_even+1)
            
            
            print('['+str(idx+1)+'R]'+"===========================")
            print(f"FL Constructor: {fl_constructor}")
            print(f"FL Driver name: {fl_driver_name}")
            print(f"FL Driver Rank: {fl_driver_rank}")
            
            sql = "insert into FL_effect (year, Round, FL_constructor, FL_driver, FL_rank) values (%s, %s, %s, %s, %s);"
            cur.execute(sql, (int(year), int(idx+1), fl_constructor, fl_driver_name, fl_driver_rank))
            remote.commit()

        except:
            continue
        
        # from past team name to current team name.
        if "Alfa Romeo Ferrari" in constructor_in_each_year:
            constructor_in_each_year["Kick Sauber Ferrari"] = constructor_in_each_year.pop("Alfa Romeo Ferrari")
        elif "Alfa Romeo Racing Ferrari" in constructor_in_each_year:
            constructor_in_each_year["Kick Sauber Ferrari"] = constructor_in_each_year.pop("Alfa Romeo Racing Ferrari")
        elif "AlphaTauri Honda RBPT" in constructor_in_each_year:
            constructor_in_each_year["RB Honda RBPT"] = constructor_in_each_year.pop("AlphaTauri Honda RBPT")
        elif "Scuderia Toro Rosso Honda" in constructor_in_each_year:
            constructor_in_each_year["RB Honda RBPT"] = constructor_in_each_year.pop("Scuderia Toro Rosso Honda")
        elif "AlphaTauri Honda" in constructor_in_each_year:
            constructor_in_each_year["RB Honda RBPT"] = constructor_in_each_year.pop("AlphaTauri Honda")
        elif "McLaren Renault" in constructor_in_each_year:
            constructor_in_each_year["McLaren Mercedes"] = constructor_in_each_year.pop("McLaren Renault")
        elif "Red Bull Racing Honda" in constructor_in_each_year:
            constructor_in_each_year["Red Bull Racing Honda RBPT"] = constructor_in_each_year.pop("Red Bull Racing Honda")
        elif "Red Bull Racing RBPT" in constructor_in_each_year:
            constructor_in_each_year["Red Bull Racing Honda RBPT"] = constructor_in_each_year.pop("Red Bull Racing RBPT")
        elif "Renault" in constructor_in_each_year:
            constructor_in_each_year["Alpine Renault"] = constructor_in_each_year.pop("Renault")
        elif "Racing Point BWT Mercedes" in constructor_in_each_year:
            constructor_in_each_year["Aston Martin Aramco Mercedes"] = constructor_in_each_year.pop("Racing Point BWT Mercedes")
        elif "Aston Martin Mercedes" in constructor_in_each_year:
            constructor_in_each_year["Aston Martin Aramco Mercedes"] = constructor_in_each_year.pop("Aston Martin Mercedes")
        elif "Racing Point BWT Mercedes" in constructor_in_each_year:
            constructor_in_each_year["Aston Martin Aramco Mercedes"] = constructor_in_each_year.pop("Racing Point BWT Mercedes")

        constructor_in_total[f"{year}"] = constructor_in_each_year
        
    print(constructor_in_total)


df = pd.DataFrame(constructor_in_total).fillna(0)

plt.figure(figsize=(20, 12))
sns.heatmap(df.T, annot=True, fmt=".0f", cmap="OrRd", cbar_kws={'label': 'Score'})
plt.title("Yearly Fastest Lap Records")
plt.xticks(rotation=30, fontsize=8)
plt.yticks(rotation=0)
plt.xlabel("Constructors")
plt.ylabel("Years")
plt.show()

plt.show()
print(df)

remote.close()