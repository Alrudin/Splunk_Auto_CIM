# Future Work & Tech Debt

## GitOps and Deployment
- **GitLab Integration**: Initially, generated `.conf` files are written directly to a mounted local volume (`./apps`) for immediate testing. In the future, the deployment module must integrate with the GitLab API to:
  1. Commit the `.conf` files to a new branch.
  2. Create a Merge Request (MR).
  3. Rely on a GitLab CI/CD pipeline running `splunk-appinspect` to validate the configurations.
  4. Wait for analyst review and merge before final deployment to the Splunk instance.
