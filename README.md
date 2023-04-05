-> **ENGLISH / INGLÊS:** This application will soon be deployed and this file will be translated to portuguese. / **PORTUGUESE / PORTUGUÊS:** Em breve será realizado o deploy desta aplicação e este arquivo será traduzido para o português.

# FINANCE

A Web Application that queries the [IEX](https://www.iexexchange.io/products/market-data-connectivity) API for some stock prices and allows the user to buy or sell them based in the latest prices. The user can have profits or losses based on those prices. Each user can sign up and have his or her own session to manage his or her portfolio of stocks. 

## Description:

This software was developed during the **problem set 9 of cs50** and some extra funtionality were added for this final project. First i'll talk about, briefly, the implementation that cs50 already made for us to start developping on the existing project, then, i'll talk about what i did and my design ideas.

So, in the file **helpers.py**, cs50 defined 4 functions: <u>apology</u>, that is used to generate error messages on the interface if something goes wrong; <u>login_required</u>, that creates a function decorator to check if the user is logged in; <u>lookup</u>, that implement the integration with the **IEX API**; and <u>usd</u>, that transforms float numbers into USD format.
In the **templates folder**, cs50 already made the files **layout.html**, that just creates the model for the interface to be used in all html files, the **login.html** that have a form for the user to try to login into the system, the **register.html** that has another form for the user to registrate into the system and the **apology.html**, that renders the error messages.
In the **app.py** file, we have some initial configuration for the Flask app, the usage of the API, the database, the session and the usd function. Cs50 already created the <u>after_request</u> function and the <u>routes for the login and logout</u>.

**Now the features that i implemented**. Still in **app.py**, the <u>register route</u> both creates a new user via POST method, validating all the inputs and storing the login and the hashed password in the users table of **finance.db**, and renders the **register.html** template via GET method. After registration the user is redirected to the login page and if the inputed informations are ok, the system will redirect to the index page of that particular user.

On the <u>index route</u> will appear a portfolio of the user, showing all the shares that he or she owns, the cash available and the grand total, that is the sum of the cash with the current price of all shares. To show this, the route uses both the transactions table of the **finance.db** and the current status of all the shares, the informations are processed and submited to the **index.html** template to be rendered using Jinja.

The <u>quote route</u> is for both searching for the shares of a particular company via POST and to render the template **quoted.html** that shows the UI for that page with the query results.

The <u>buy route</u> is similar to the quote one, the difference is that now the user will be able to purchase a share based on the cash amount. All the data received via POST will be validated and, if all goes right, the cash will be updated and the transactions table will have a new row with all the information of that particular transaction, including date and time. It's important to note that all of this functionality is based on the session, so the system are keeping track of the user that is logged in.

The <u>sell route</u> is also very similar to the buy one, the only difference is the restriction that the user only can sell what he or she owns. The transactions table, in this case, will receive a new row but in the shares column the number will be inserted multiplied by minus one. For the GET method of this particular route, a template with all the shares that the user owns will be rendered using the select and option tags.

The <u>history route</u> will basically render the transactions table of the **finance.db** file on the screen, in the **history.html** file.

Finally, the <u>change_password route</u> will just render a page for the users to change their password via GET method and if the inputs, submited via POST method, are correct, his or her password will be updated on **finance.db**, a visual feedback will appear on the screen using the <u>flash</u> method, and the page will be redirected to the <u>index route</u>.