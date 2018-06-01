#! /bin/bash

HEAD=$(cat <<-END
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Reports</title>
  </head>
  <body>
    <h1>Solsa reports</h1>
    <ul>
END
)


TAIL=$(cat <<-END
    </ul>
  </body>
</html>
END
)

LINKS=""

for p in *.sol.html; do
  LINKS+="
      <li><a href=\"${p}\">${p%.*}</a></li>"
done

echo "${HEAD}${LINKS}${TAIL}"