#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess

def download_TROPOMI(startdate, enddate, Sat_datadir):
    """
    Download TROPOMI data from AWS for desired dates.

    Arguments
        startdate    [np.datetime64]  : Start date of download range
        enddate      [np.datetime64]  : End date of download range
        Sat_datadir  [str]            : TROPOMI data directory for storing data

    """
    # offline: 11/28/18 to end of 2020? + parts of 01/21
    # s3://meeo-s5p/OFFL/L2__CH4___/2018/MM/DD/*.nc
    # reprocessed: 04/30/18 to 11/28/18
    # s3://meeo-s5p/RPRO/L2__CH4___/2018/MM/DD/*.nc
    # --no-sign-request
    start_str = str(startdate)
    start_year = start_str[:4]
    start_month = start_str[5:7]
    start_day = start_str[8:10]

    end_str = str(enddate)
    end_year = end_str[:4]
    end_month = end_str[5:7]
    end_day = end_str[8:10]

    DATA_DOWNLOAD_SCRIPT='./auto_generated_download_script.sh'
    cmd_prefix = "aws s3 sync "
    remote_root = "s3://meeo-s5p/"
    # access number of days in each month easily
    month_days = [31,[28,29],31,30,31,30,31,31,30,31,30,31]
    with open(DATA_DOWNLOAD_SCRIPT, "w") as f:
        print("#!/bin/bash\n", file=f)
        print("# This script was generated by jacobian.py\n", file=f)

        for year in range(int(start_year), int(end_year)+1):
            # skip years with definite no data
            if year<2018:
                print('Skipping TROPOMI data download for ', str(year),
                      ': no data from this year')
                continue
            init_month=1
            final_month=12
            if year==int(start_year):
                # only get desired months from incomplete years
                init_month=int(start_month)
            if year==int(end_year):
                final_month=int(end_month)
            for month in range(init_month, final_month+1):
                # skip months with definite no data
                if year==2018 and month<4:
                    print('Skipping TROPOMI data download for ', str(year),
                          '/0', str(month), ': no data from this month')
                    continue
                # add 0 to month string if necessary
                month_prefix = '0' if month<10 else ''
                init_day=1
                final_day=month_days[month-1]
                # leap day
                if month==2:
                    if year%4==0:
                        final_day=final_day[1]
                    else:
                        final_day=final_day[0]
                if month==int(start_month) and year==int(start_year):
                    # only get desired days from incomplete months
                    init_day=int(start_day)
                if month==int(end_month) and year==int(end_year):
                    final_day=int(end_day)

                for day in range(init_day, final_day+1):
                    # skip days with definite no data
                    if year==2018 and month==4 and day<30:
                        print('Skipping TROPOMI data download for ', str(year),
                              '/0', str(month), '/', str(day), ': no data from this day')
                        continue
                    # build download string
                    download_str=cmd_prefix+remote_root
                    # add 0 to day string if necessary
                    day_prefix = '0' if day<10 else ''
                    # choose RPRO or OFFL directory based on date
                    if year==2018:
                        if month>=5 and month <=10 or (month==4 and day==30) or (month==11 and day<28):
                            download_str=download_str+'RPRO/L2__CH4___/'+str(year)+'/'+\
                                month_prefix+str(month)+'/'+day_prefix+str(day)+'/ ' + Sat_datadir
                        elif month==11 and day==28:
                            # Special case where both datasets have data from this day
                            download_str=download_str+'RPRO/L2__CH4___/'+str(year)+'/'+\
                                month_prefix+str(month)+'/'+day_prefix+str(day)+'/ ' + Sat_datadir
                            f.write(download_str)
                            f.write('\n')
                            download_str=download_str+'OFFL/L2__CH4___/'+str(year)+'/'+\
                                month_prefix+str(month)+'/'+day_prefix+str(day)+'/ ' + Sat_datadir
                            f.write(download_str)
                            f.write('\n')
                        else:
                            download_str=download_str+'OFFL/L2__CH4___/'+str(year)+'/'+\
                                month_prefix+str(month)+'/'+day_prefix+str(day)+'/ ' + Sat_datadir
                    else:
                        download_str=download_str+'OFFL/L2__CH4___/'+str(year)+'/'+\
                            month_prefix+str(month)+'/'+day_prefix+str(day)+'/ ' + Sat_datadir
                    f.write(download_str)
                    f.write('\n')

    os.chmod(DATA_DOWNLOAD_SCRIPT, 0o755)
    print("Downloading TROPOMI data from AWS")
    # Run the data download script
    # Remove the file afterwards
    status = subprocess.call(DATA_DOWNLOAD_SCRIPT)
    os.remove(DATA_DOWNLOAD_SCRIPT)

if __name__ == '__main__':
    import sys
    import datetime
    import numpy as np

    startday = sys.argv[1]
    endday = sys.argv[2]
    Sat_datadir = sys.argv[3]

    # Reformat start and end days for datetime in configuration
    start = f'{startday[0:4]}-{startday[4:6]}-{startday[6:8]} 00:00:00'
    end = f'{endday[0:4]}-{endday[4:6]}-{endday[6:8]} 23:59:59'

    # Convert to datetime64
    GC_startdate = np.datetime64(datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S'))
    GC_enddate = np.datetime64(datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=1))

    download_TROPOMI(GC_startdate, GC_enddate, Sat_datadir)