import glob
import time
import re
import os

def get_specfile_timestamp(file):
    SPEC_datetime = re.compile(r"^#D")
    timestamp = None

    datetimeformat = "%a %b %d %H:%M:%S %Y"
    with open(file) as fid:
        for line in fid:
            if SPEC_datetime.match(line):
                line = SPEC_datetime.sub("", line).strip()
                datetimestruct = time.strptime(line, datetimeformat)
                mon = datetimestruct.tm_mon
                if mon < 10:
                    mon = '0' + str(mon)
                else:
                    mon = str(mon)
                mday = datetimestruct.tm_mday
                if mday < 10:
                    mday = '0' + str(mday)
                else:
                    mday = str(mday)
                timestamp = str(datetimestruct.tm_year) + mon + mday
                break

    return timestamp


def get_file_by_timestamp(detcorrectionsdir, timestamp, pattern):
    files = glob.glob(pattern, root_dir=detcorrectionsdir)
    files.sort()
    filestamps = [file[8:16] for file in files]
    filestamps.append(timestamp)
    filestamps.sort()
    ind = filestamps.index(timestamp)
    # check for case the stamp is the same
    if len(filestamps) > ind + 1 and filestamps[ind] == filestamps[ind + 1]:
        return (os.path.join(detcorrectionsdir, files[ind]))
    elif ind == 0:
        return ""
    return(os.path.join(detcorrectionsdir, files[ind-1]))
