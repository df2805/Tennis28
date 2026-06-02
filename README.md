# Tennis Match Predictor Website

This is a GitHub Pages-ready website built from the pasted Tennis Match Predictor Colab code.

## Files

- `index.html` - static page structure
- `styles.css` - responsive visual design
- `script.js` - browser demo logic

## Publish On GitHub Pages

1. Create a new GitHub repository.
2. Add these files to the repository root.
3. Commit and push to the default branch.
4. In GitHub, open `Settings` -> `Pages`.
5. Set the source to `Deploy from a branch`.
6. Choose the default branch and `/root`, then save.

GitHub will publish the website at:

```text
https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/
```

## Notes

The original pasted code is a Python/Colab model pipeline. GitHub Pages only runs static HTML, CSS, and JavaScript, so this site includes a front-end predictor demo rather than the full XGBoost training runtime. The demo includes Grand Slam context for Roland Garros and Wimbledon.

To use the real trained model online, deploy the Python predictor behind an API, then replace the scoring function in `script.js` with a `fetch()` call to that API.
