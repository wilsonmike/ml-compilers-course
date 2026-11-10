# Deploying the site

The hosted site is the repository itself, served as static files by [Cloudflare Pages](https://pages.cloudflare.com/)
on its free plan, with no build step. The course is the home page: `_redirects` sends `/` to `/site/`.

Students still run code on their own machines with `python tools/serve.py`. On the hosted site (and on phones) the
lessons, quizzes, hints, and answers all work, and each exercise has the editor with Compare with answer, which diffs
your code against the reference answer.

## Before a deploy

```
python tools/build_static.py      # exercise data for pages without the runner
python tools/build_helpers.py     # the test guides
python tools/design_lint.py       # design and copy rules
```

Commit and push to `main`. Every push deploys again, and other branches get preview URLs.

## Cloudflare Pages (first time)

1. In the Cloudflare dashboard, open **Workers & Pages**, choose **Create**, then **Pages**, then **Connect to Git**,
   and pick the repository.
2. Build settings: framework preset **None**, build command empty, build output directory `/`.
3. Under the project's **Custom domains**, add the domain. If its DNS is on Cloudflare, the record and the certificate
   are set up for you.

`_headers` sets a few security headers and serves the specs and tests as plain text. `404.html` is the page for
links that don't exist. Pages serves `/x.html` at `/x`, and `site/assets/course.js` matches lessons under either.

## Costs

Cloudflare Pages is free for a static site. The only fixed cost is the domain.
