# Deploy


**It is strongly recommended to use `git` to track your files for ease of deploying to your favourite hosting provider**

After you have done creating your website, **stop** `vai run` and now run

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

Nonetheless,  it should work for **most** other hosting provider as well as you would just need link your `build output` to the root of the `dist/` directory. We will only cover how to deploy to the 4 hosting providers mentioned above. If you prefer to use a different hosting provider, please refer to their documentation and follow the necessary steps.




## Vercel
1. `Sign` up or log in to Vercel.
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
6. Configure Build Settings. In Build output directory, choose the path to your	`dist/` directory
7. Save and Deploy:


## Github Pages
[Official guide](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)

*Some key things to take note of* :

1. github pages only allows the website to be hosted on either `docs/` or your project root dir
2. You would have to change the `dist/` directory to `docs/` or host a seperate github repo and transfer everything inside of  `dist/` there  