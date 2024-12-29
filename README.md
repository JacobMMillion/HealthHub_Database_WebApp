# HealthHub: A Web Application for Disease Tracking and Discussion

**Created by Jacob Million and Michael Carrion**  
*For COMS4111: Databases - Columbia University*

---

## Overview
**HealthHub** is a web application implemented in Python with Flask designed to help users monitor diseases in specific states and engage in discussions about health-related topics. Users can:  
- Track diseases and the states they are interested in.  
- Post questions to a discussion board and reply to others.  
- View statistics, including the number and type of diseases in each state.  
- Identify the riskiest state based on the total number of reported diseases.  

---

## Application Features
### Home Page
The home page provides quick access to key features, including:  
- Links to disease statistics by state.  
- Information on the riskiest state, determined by disease count.  

### Discussion Board
A platform for users to:  
- Ask health-related questions.  
- Share insights and provide responses to other users' questions.  

### Disease Statistics Table
Users can explore detailed data, including:  
- Disease counts by state.  
- Breakdown of disease types.  

---

## Database Design
HealthHub is built on a relational database, visualized through the following ER diagram:  
![ER Diagram](https://github.com/user-attachments/assets/2dd5c50b-631e-4c3f-b487-07297594406e)

---

## Screenshots
### Web Application Interface
When the server is up and running, the application interface appears as follows:  
![Web App Interface](https://github.com/user-attachments/assets/e370c25d-5d9b-4943-89c4-99224c91fda5)

### Discussion Board
An example of the discussion board interface:  
![Discussion Board](https://github.com/user-attachments/assets/e7fc3d9d-dc34-4339-8363-3b0edaae7c44)

### Disease Statistics Table
Example data for disease count in New York:  
![Disease Table](https://github.com/user-attachments/assets/ae32ec91-79a0-46d2-8471-c5985b1d46b6)

---

## Reference
This application is based on the instructions provided in the following repository:  
[GitHub Project Instructions](https://github.com/w4111/project1-f24/blob/main/part3.md)
