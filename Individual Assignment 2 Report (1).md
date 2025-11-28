# **Individual Assignment 2 Report**

## **Intro**

From the last Assignment, I created a minimal blog application using Flask and SQLite. The app allowed users to create, edit, view, archive and delete posts through a simple web interface, and stored all data in a local SQLite database via SQLalchemy. I also used Github to continuously push my local repo to my online repo so all changes were saved online, and easy to share.

This second assignment focused on improving my app from a DevOps POV. The goals are to improve code quality and testing, add proper CI/CD, and expose health and monitoring checks. Concretely, I changed parts of my code and redesigned it to avoid code smells. I applied a test suite and used Github actions to check the tests and fail on purpose if the coverage was below 70%. I also containerized the application and set up automation via Azure web app. Finally, I added health and metric endpoints through a “Prometheus-style”.

This report is organised around the assignment requirements: code quality and testing improvements, CI (Continuous Integration), CD (Continuous Deployment) through Azure, monitoring and health checks, and finally a short reflection on areas for improvement. 

## **Code Quality and Testing**

### Refactoring & Code Quality Improvements

To improve the code quality of my application, I reviewed the original implementation for duplicated code, hard-corded values, and tightly coupled functions. I would first identify and report specific code sections that had any code smells (bloater, shotgun surgery, etc.), then I would analyze the code and see how I can improve it with SOLID principles and Claude AI suggestions. The code was not to rewrite the application, but to make targeted improvements while making the codebase simple and readable.

One specific example is the separation of responsibilities between the Flask app factory (*create\_app*) and the database logic. This reinforces the **SRP** (Single Responsibility Principle), making the app easier to test and configure.

Another example is how I moved metrics hooks into their own defined functions such as *before\_request, after\_request,* and *teardown\_request*), which makes them reusable and keeps route handlers focused only on business logic.

Also, the addition of *log\_action()* helper function also reduces duplication of code in admin routes, improving maintainability and readability.

These changes applied the SOLID principles where they were appropriate, reduced the smell, and improved readability and simplicity across the app.

### Testing Strategy

The project includes a small but focused test suite using pytest. The main goal is to smoke-test the most important routes and catch obvious regressions whenever I change the code.

The test covered:

- Loading public homepage (/)  
- Loading the admin dashboard (/admin)  
- Creating a POST through /admin/posts/new and confirming it appears on the page.  
- Hitting the remaining admin routes (/admin/history, edit, delete, archive, unarchive, and view post) and verifying that they respond gracefully even when the post ID does not exist (status in 200/302/404)  
- Calling the new /health endpoint and checking that it returns HTTP 200 with a JSON body containing status, request\_count, error\_count, and avg\_latency\_ms

These tests give feedback that the main routes are correctly implemented and that the new health endpoint behaves as expected. Combined with the coverage gate in CI, the tests help prevent accidental breakages when adding new features.

### Code Coverage

Another key requirement was to enforce a minimum of 70% test coverage. This was implemented via pytest and the *coverage* Python package.

We also used Github Actions CI pipeline which was configured to:

1. Run all tests on every push  
2. Generate a coverage report  
3. Fail if the code was below 70%

This ensures that future changes cannot reduce test quality without being noticed.

## **Continuous Integration (CI)**

For this part of the assignment, I implemented a full CI pipeline using Github Actions as mentioned. The workflow was defined through the ci.yml file and is automatically triggered for every push to the repo in any branch. This ensures that no code is merged or deployed without passing the checks.

The CI pipeline runs three main stages:

#### **1\. Test**

* The pipeline installs all dependencies (including dev dependencies)  
  Runs the pytest test suite  
* The workflow fails immediately if any test fails  
* Coverage is also checked to ensure code quality does not regress

#### **2\. Build (Docker)**

* After tests pass, the CI builds a Docker image of the Flask application  
* This validates:  
  * That the Dockerfile works correctly  
  * That dependencies are correctly installed  
    That the app fully builds in a clean environment  
* The build job also uploads the image as a CI artifact

#### **3\. Deployment**

* The final job deploys the app **only when changes are pushed to the main branch**  
* It uses GitHub’s azure/webapps-deploy action  
* Secrets for Azure credentials are stored securely in GitHub Actions variables  
* This makes deployment **fully automatic**, with no manual steps  
* (more on this later on the CD section)

## **Continuous Deployment (CD)**

For this part, I implemented a fully automated CD pipeline, using both Github Actions and Azure Web App. The deployment is only triggered when changes reach the main branch, ensuring that only reviewed and approved code is ever deployed.

**Deployment Pipeline Overview**  
Once the CI steps (test \+ Docker build) successfully pass, the CD stage takes over, like a true CI/CD app:

1. **Runs the same DockerBased Build used in CI**  
   1. Ensures the deployed application is identical to the one that passed all the tests  
2. **Deploys automatically to Azure Web App**  
   1. Uses the official azure/webapps-deploy@v2 Github Action  
   2. Publishes the Docker image/code bundle to the cloud  
3. **Secure Credentials Handling**  
   1. Used GitHub actions secrets to avoid hardcoding tokens or passwords in the repo  
   2. E.g.: “AZURE\_WEBAPP\_PUBLISH\_PROFILE”  
4. **Main Branch protected**  
   1. Only main branch triggers the deployment  
   2. Feature branch must go through Pull Requests

**Result**  
The app is now continuously deployed to:  
[https://daniel-blog-code-d0ddbmd2h3e8hxfq.westeurope-01.azurewebsites.net/](https://daniel-blog-code-d0ddbmd2h3e8hxfq.westeurope-01.azurewebsites.net/)  
Every change merged into main is automatically:

- Built  
- Tested  
- Packaged  
- Deployed

## **Monitoring and Health Checks**

To meet the observability requirements, I added both a health endpoint and Prometheus metrics instrumentation to the application. This allows outside systems and people to see whether the app is working and how well it is performing.

**Health Check Endpoint**  
I implemented the endpoint “/health”. This endpoint returns a live application status as shown below in the screenshot:  
\[SCREENSHOT 1\]

It Provides:

- A simple “ok” vs “not ok” signal  
- Internal counters for errors and requests (currently 0 errors as shown)  
- Measured “avg\_latency\_ms” which is what it describes

This can be used by Azure for restarts or autoscaling, while also working as a readiness and liveness probe for containers.

**Prometheus Metrics Endpoint**  
I also added a second endpoint “/metrics”. This endpoint exposes the app-level metrics in Prometheus format as shown below:  
\[SCREENSHOT 2\]  
This includes the total number of requests, requests per end-point, Error count, latency distributions, process memory, CPU time, and Python GC metrics for example.

## **Conclusion**

This assignment transformed the basic Flask blog application into a fully containerized and observable system aligned with DevOps practices. Via automated tests, we ensure over 70% code coverage, and the introduction of Docker made the application environment friendly across development and deployment. The CI/CD implementation via GitHub actions and Azure Web Services enabled seamless integration and delivery, eliminating the need for manual deployment and avoiding errors. Last but not least, we also introduced runtime health checks and Prometheus metrics to provide real-time visibility and monitoring to the public. Overall, this project shows how even a simple web application can and should follow DevOps practices.