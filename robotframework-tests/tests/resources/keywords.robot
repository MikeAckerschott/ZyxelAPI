*** Keywords ***
Run Zyxel Script
    [Arguments]    @{args}
    ${result}=    Run Process    python    ${CURDIR}/../../src/requestCallHistory.py    @{args}    stdout=PIPE    stderr=PIPE
    Set Test Variable    ${OUTPUT}    ${result.stdout}
    Set Test Variable    ${RC}        ${result.rc}

Should Contain Output
    [Arguments]    ${text}
    Should Contain    ${OUTPUT}    ${text}
