# Docusaurus

## Table Of Contents

# Setup

1. Step : **Run the following**

   - You can run this command anywhere in a new empty repository or within an existing repository, it will create a new directory containing the scaffolded files.
     ```sh
        npx create-docusaurus@latest <app-name> classic
     ```
   - The `classic` template is recommended so that you can get started quickly, and it contains features found in Docusaurus 1. The `classic` template contains `@docusaurus/preset-classic` which includes standard documentation, a blog, custom pages, and a CSS framework (with dark mode support). You can get up and running extremely quickly with the classic template and customize things later on when you have gained more familiarity with Docusaurus.

2. Step : **Project structure**

   - Assuming you chose the `classic` template and named your site `<app-name>`, you will see the following files generated under a new directory `<app-name>/`:
     - `<app-name>`
       - blog
       - docs
       - src
       - static
       - docusaurus.config.js
       - package.json
       - README.md
       - sidebars.js
       - yarn.lock
     - where:
       - `/blog/` - Contains the blog Markdown files. You can delete the directory if you've disabled the blog plugin, or you can change its name after setting the `path` option. More details can be found in the [blog guide]()
       - `/docs/` - Contains the Markdown files for the docs. Customize the order of the docs sidebar in `sidebars.js`. You can delete the directory if you've disabled the docs plugin, or you can change its name after setting the `path` option. More details can be found in the [docs guide]()
       - `/src/` - Non-documentation files like pages or custom React components. You don't have to strictly put your non-documentation files here, but putting them under a centralized directory makes it easier to specify in case you need to do some sort of linting/processing
         - `/src/pages` - Any JSX/TSX/MDX file within this directory will be converted into a website page. More details can be found in the [pages guide]()
       - `/static/` - Static directory. Any contents inside here will be copied into the root of the final build directory
       - `/docusaurus.config.js` - A config file containing the site configuration. This is the equivalent of `siteConfig.js` in Docusaurus v1
       - `/package.json` - A Docusaurus website is a React app. You can install and use any npm packages you like in them
       - `/sidebars.js` - Used by the documentation to specify the order of documents in the sidebar

3. **Step** : **Running the development server**

   - To preview the changes, run:
     ```sh
        cd <app-name>
        npm run start
     ```
   - By default, a browser window will open at http://localhost:3000.

4. **Step** : **Build**
   - Docusaurus is a modern static website generator so we need to build the website into a directory of static contents and put it on a web server so that it can be viewed. To build the website:
     ```sh
        npm run build
     ```

# Deployment

## 1. Deploy to GitHub Pages

- Run:
  ```sh
   npm run deploy
  ```

# Resources and Further Reading

1. [docusaurus - docs](https://docusaurus.io/docs)
