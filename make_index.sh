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
END
)


TAIL=$(cat <<-END

  </body>
</html>
END
)

LINKS=""

for p in *.sol.html; do
  LINKS+="
    <a href=\"${p}\">${p%.*}</a><br/>"
done

echo "${HEAD}${LINKS}${TAIL}"