*** Settings ***
Library    Process
Library    OperatingSystem
Resource   resources/keywords.robot
Resource   resources/variables.robot

*** Test Cases ***
Run Zyxel With Body File
    Run Zyxel Script    --body    ${BODY_FILE}    --insecure
    Should Contain Output    Login successful
    Should Contain Output    Saved call history
    File Should Exist    ${OUTPUT_FILE}
