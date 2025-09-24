*** Variables ***
${ROUTER_IP}          192.168.1.1
${LOGIN_URL}          https://${ROUTER_IP}/UserLogin
${CALLHISTORY_URL}    https://${ROUTER_IP}/cgi-bin/CallHistory?action=Backup

${BODY_FILE}          ${CURDIR}/../../data/body.json
${OUTPUT_FILE}        ${CURDIR}/../../CallHistory
