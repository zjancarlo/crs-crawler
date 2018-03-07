# crs-crawler
UPD CRS Crawler that generates CSV with course name, instructor, location, schedule, and estimated enrolled students. Useful for scheduling promotional room-to-room activities.

## Running the Crawler
Open up your Python interpreter, import crs_catalogcrawler and run runCrawler()

## Updating for the current semester
Update the baseURL variable inside the sched_crawl function. Check https://crs.upd.edu.ph/schedule/ for the new base URL.

## Disclaimer
This code was initially created to work on the 2nd Sem 2016-2017 layout of CRS. It seems to work fine as of 2nd Sem 2017-2018 but there are no guarantees that the data is error-free.
