# Deploy

:::tip TIP
It is strongly recommended to use git to track your files for ease of deploying to your favourite hosting procider
:::
After you have done creating your website, stop `vai run` and now run

```
vai build
``` 

:::info If you plan on deploying to github pages instead, run
```
vai build ---github
```
:::

After that, you would notice a `dist/` folder at the root of your directory which contains all your minified `html`, `css`, `js` and `search_index.json` files. You should use this to deploy to your favourite hosting provider. 
`vai` has been tested successfully on 

1. [vercel](https://vercel.com/)
2. [netlify](https://www.netlify.com/)
3. [cloudfare pages](https://pages.cloudflare.com/)
4. [github pages](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)

But it should work for **most** other hosting provider as well as you would just need link your `build output` to the root of the `dist/` directory. We will only cover how to deploy to the 4 hosting providers mentioned above. If you prefer to use a different hosting provider, please refer to their documentation and follow the steps provided there.


## Vercel

## Netlify

## Cloudfare Pages
1. create an account at cloudfare pages
2. create application
3. It will pick workers by default, choose Pages

Now u can either  `direct upload` or `import a existing git repository`. It is recommended to pick the latter if you have been using git to track your site.

If you pick `import a existing git repository`, just follow the onsite instructions. You can leave most of the options to its defualt option. all you have to do is link ur `dist/` folder in the `Build output directory` box

 


## Github Pages



## Vercel
1. Sign up or log in to Vercel.
2. Click Add New... > Project.
3. Import the Git repository containing your `vai` project.
4.  Click Deploy. Vercel will build and deploy your site.
Netlify
Netlify is another popular and powerful platform for deploying static sites.
Create a New Site:
Sign up or log in to Netlify.
From your dashboard, click Add new site > Import an existing project.
Connect to your Git provider and select your project's repository.
Configure Build Settings:
Netlify will ask for your build settings. Enter the following:
Setting	Value
Build command	vai build
Publish directory	dist
Deploy Site:
Click Deploy site. Netlify will handle the rest.
Cloudflare Pages
Cloudflare Pages leverages its massive global network for incredible speed.
Create a Pages Project:
Sign up or log in to your Cloudflare dashboard.
In the sidebar, navigate to Workers & Pages.
Click Create application > select the Pages tab > Connect to Git.
Select Your Repository:
Choose the repository for your vai project and click Begin setup.
Configure Build Settings:
This is the most important step. In the "Build settings" section, enter the following:
Setting	Value
Build command	vai build
Build output directory	dist
Save and Deploy:
Click Save and Deploy. Your site will be live in minutes