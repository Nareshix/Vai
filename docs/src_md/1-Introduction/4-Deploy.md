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
4. edit the root directory and pick `dist`
5. Click Deploy.

## Netlify
1. Sign up or log in to Netlify.
2. From your dashboard, click Add new project > Import an existing project.
3. Connect to your Git provider and select your project's repository.
4. In Build Settings, go to publish directory and write the path to the `dist/` folder

## Cloudflare Pages
1. Sign up or log in to your Cloudflare dashboard.
2. In the sidebar, navigate to Workers & Pages.
3. Click Create application > select the Pages tab > Connect to Git.
4. Select Your Repository:
5. Choose the repository for your vai project and click Begin setup.
6. Configure Build Settings:
This is the most important step. In the "Build settings" section, enter the following:
Setting	Value
Build command	vai build
Build output directory	dist
Save and Deploy:
Click Save and Deploy. Your site will be live in minutes