# Authorization_Checking_URL_Crawler<br>
**Aim:** The aim of this scanning tool is to scan all the links in an application with different privileges and should check if any of the links are allowing authorization bypass through privilege escalation.<br>
1. The code scans the paths mentioned in each different user profiles after login and will detect the common links in both the privileges, allowing us to verify if there any links are added which are not actually supposed to be added.<br>
2. To check if there is any possibility for authorization bypass, I used IDOR testing logic, such that the code will scan the paths that have ids passed in the URLs.<br>
3. Taking these paths it will check if the privilege escalation is possible with credential swapping.<br>
<br>**Example Scenario:**<br>
User 1 can access Admin. User 2 can access User 1. Admin can access User 1, User 2<br>
![Screenshot_1](https://github.com/user-attachments/assets/fdaaa62e-38dc-4347-aa2a-415696a755f8) <br>
-> I designed a simple application that is vulnerable to authorization bypass using Flask in visual studio (only runs on local host). The application contains 3 roles, with each role having 2 internal paths.<br>
-> The scanning code uses Selenium to perform the automatic login and scanning.<br>
-> The code takes the login URLs, credentials and performs the scan.The output consists of internal paths in each role, possible IDOR urls and status of authorization bypass.<br>
-> The Code when executed will start the Selenium generated chrome window and asks for the input parameters. You will be seeing something like this.<br>
![Picture1](https://github.com/user-attachments/assets/4812d3c3-f337-4243-8be7-49ce5fe71e60)<br>
-> Taking the input, the output will look like this:<br>
![Picture2](https://github.com/user-attachments/assets/047eb835-d38f-4e57-aca5-ced06c03f008)<br>
![Picture3](https://github.com/user-attachments/assets/040d7915-8c45-497e-b9f2-4d2ed48ed8a6)<br>

**Note:** This code is still under development and works better for static applications rather than complex dynamic applications. Also note that this code cannot bypass captcha, reCaptcha or OTP. 





