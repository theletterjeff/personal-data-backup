#!/bin/bash
# This script is a one-time-use tool for backfilling Last.fm data one month
# at a time.

# Start and end years and months
start_year=2006
start_month=5  # May
end_year=2024
end_month=10  # October

# Current year and month
current_year=${start_year}
current_month=${start_month}

while [[ ${current_year} -lt ${end_year} ]] || [[ ${current_year} -eq ${end_year} && ${current_month} -le ${end_month} ]]; do

  # Formatting current year and month to YYYY-MM format
  ym=$(printf "%04d-%02d" ${current_year} ${current_month})

  # First second of the first day of the month
  start_of_month_sec=$(date -ju -f "%Y-%m-%d %H:%M:%S" "${ym}-01 00:00:00" +"%s")

  # Last second of the last day of the month
  # Find the first day of the next month, then subtract 1 second
  if [[ ${current_month} -eq 12 ]]; then
    next_month_year=$((current_year + 1))
    next_month=1
  else
    next_month_year=${current_year}
    next_month=$((current_month + 1))
  fi
  next_ym=$(printf "%04d-%02d" ${next_month_year} ${next_month})
  end_of_month_sec=$(($(date -ju -f "%Y-%m-%d %H:%M:%S" "${next_ym}-01 00:00:00" +"%s") - 1))

  payload=`echo "{\"start\": $start_of_month_sec, \"end\": $end_of_month_sec}" | openssl base64`
  aws lambda invoke \
      --function-name PersonalDataBackupStack-BackupHandlerAC91A874-SL2j8qQwtDrI \
      --payload $payload \
      response.json

  # Increment month
  if [[ ${current_month} -eq 12 ]]; then
    current_year=$((current_year + 1))
    current_month=1
  else
    current_month=$((current_month + 1))
  fi

  echo "$current_month $current_year complete"
done
