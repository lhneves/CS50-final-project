# Doretto Stock #
#### Video Demo:  <https://youtu.be/jufRD80WXM0>

#### Description:

#### My project is an extension of the finance problem set, it starts with a responsive landing page, that explains how the stock market works and invite you to crate an account.

#### When you click to start now and create an account, it will have a fully responsive page including login, register and recover password pages.

#### After login, a page with a table content that shows your stocks shares is presented, along with a graph of how many percent each share represents in your portfolio.

#### We also have the quote, buy, sell and history pages. My focus was on the responsive and front-end design, I hope you like it.

#### In the static folder we have the css, image and javascript folders. The css folder contains the diferent design for diferent pages: buy.css (designs for buy.html, sell.html and quote.html), index.css (designs for index.html and history.html), login.css (design for login.html), register.css (design for register.html and change.html), style.css (design for page.html). I used the blue color because it means trust and it's good for a marketplace and used the @media screen to make the page responsive.

#### The img folder contains all the images used on this project, all png (didn't get any svg because i would need to put in my principal code and it would be extensive) and jpg (all images were taken from the freepik website, and the authors are quoted on the website).

#### The js folder contains the javascript code. I used javascript to make the website nore interactive. If the website is accessed from a device with less than 768px wide, it will show a menu toggle, the javascript code will show you the page sections if you click on that toggle.

#### It will also remove this menu section if you click elsewhere on the screen. Finale it will transform the nav title color section as you browse the site, so if you are in the about section the "About" at the navegation bar will turn blue, and so on.

#### In the templates folder have all the html files, only the layout.html is different because is the base code to buy, change, sell, quote, history and index html files.

#### The application.py is used to monitor the registration, login, password change, purchase, sale, transaction history in the database. Also to be able to login, logout and direct to all these pages.

#### The finance.db stores in 3 tables all the users, the user's transactions and their purchased shares.
#### The helpers.py is used for three functions: to search for the stock value and its data (lookup), to define that the user needs to be logged in (login_required) and to transform the stock values into dollars (usd)
