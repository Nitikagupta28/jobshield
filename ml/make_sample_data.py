"""
make_sample_data.py
-------------------
Creates a SYNTHETIC dataset so the whole project runs end to end on day one.

IMPORTANT: for your final resume version, replace data/jobs.csv with the real
"Fake Job Postings" (EMSCAD) dataset from Kaggle. It has the same column names
used here (title, company_profile, description, requirements, benefits,
fraudulent), so train.py works on it without any code change.
"""
import random
from pathlib import Path

import pandas as pd

random.seed(42)

# ---------- building blocks for LEGIT postings ----------
LEGIT_TITLES = [
    "Software Engineer", "Data Analyst", "Frontend Developer", "Backend Developer",
    "QA Engineer", "DevOps Engineer", "Business Analyst", "Product Designer",
    "Marketing Executive", "HR Associate", "Customer Support Associate",
    "Machine Learning Engineer", "Technical Writer", "Accountant", "Sales Executive",
]
LEGIT_COMPANY = [
    "{c} is a product company with over {n} employees building software for logistics, banking and healthcare customers.",
    "Founded in {y}, {c} helps retailers manage inventory and supply chains with cloud tools. We have offices in Bengaluru, Pune and Hyderabad.",
    "{c} is a mid-sized consulting firm serving enterprise clients across India and Europe with a team of {n} professionals.",
]
LEGIT_DESC = [
    "You will work with a cross-functional team to design, build and maintain features used by thousands of customers. You will participate in code reviews, sprint planning and regular retrospectives.",
    "The role involves analysing business data, building dashboards and presenting insights to stakeholders every month. You will collaborate with engineering and product teams.",
    "You will own the delivery of assigned modules, write clean documented code, add tests and help mentor interns. Reporting to the engineering manager.",
    "Responsibilities include handling client queries, maintaining documentation, coordinating with internal teams and preparing weekly reports for the department head.",
]
LEGIT_REQ = [
    "Bachelor's degree in Computer Science or a related field. 1-3 years of experience with Python, SQL or Java. Good communication skills.",
    "BCA, B.Tech or equivalent. Knowledge of data structures, databases and version control with Git. Experience with REST APIs is a plus.",
    "Strong analytical skills, proficiency in Excel and SQL, and the ability to work in a team. Prior internship experience preferred.",
]
LEGIT_BEN = [
    "Health insurance, paid leave, learning budget, hybrid work and annual performance bonus.",
    "Provident fund, medical cover, flexible hours and paid training programs.",
    "Competitive salary, team outings, health insurance and career growth plans.",
]
COMPANY_NAMES = ["Northwind Tech", "BlueOrbit Systems", "Finlytics", "CloudNest", "Kiwi Logistics",
                 "Orchid Health", "Brightpath Consulting", "Zenith Retail", "DataLoom", "Pixel Forge"]

# ---------- building blocks for FAKE postings ----------
FAKE_TITLES = [
    "Work From Home Data Entry", "Online Typing Job", "Earn Money Online", "Part Time Home Based Job",
    "Urgent Hiring Fresher", "Simple Copy Paste Work", "Customer Care Executive Home Based",
    "Ad Posting Job", "Packing Job At Home", "Software Trainee Direct Joining",
]
FAKE_DESC = [
    "Earn Rs 50000 per week working only 2 hours a day from your mobile phone. No interview, no experience needed. Limited seats, apply immediately and start earning today!!!",
    "Urgent requirement! Simple typing work from home. Registration fee of Rs 999 refundable after first week. Contact us on WhatsApp now to confirm your seat.",
    "Direct joining without interview. Pay a small security deposit for your laptop and training kit. Guaranteed income, unlimited earning, 100 percent genuine offer.",
    "We are hiring freshers for copy paste jobs. Share your Aadhaar, PAN and bank account details to receive your joining letter. Salary credited daily.",
    "Make lakhs from home with no investment risk. Just forward our messages to your contacts. Telegram us now. Hurry, only few vacancies left!!!",
]
FAKE_REQ = [
    "No qualification required. Anyone can apply. Must have smartphone and bank account.",
    "10th pass or above. No experience needed. Pay processing fee to confirm your job.",
    "Just need a mobile phone and WhatsApp. Age 18 plus. Immediate joining after payment.",
]
FAKE_BEN = [
    "Daily payment, huge incentives, work from anywhere, no targets, guaranteed bonus.",
    "Earn unlimited money, free mobile phone gift, instant salary.",
    "",
]
FAKE_PROFILE = [
    "",
    "We are a leading international company. Contact hr.jobs2024@gmail.com for details.",
    "Top global firm. Send resume on WhatsApp +91 9XXXXXXXXX.",
]


def legit_row():
    c = random.choice(COMPANY_NAMES)
    return {
        "title": random.choice(LEGIT_TITLES),
        "company_profile": random.choice(LEGIT_COMPANY).format(c=c, n=random.choice([80, 250, 600, 1200]), y=random.choice([2008, 2012, 2016, 2019])),
        "description": random.choice(LEGIT_DESC),
        "requirements": random.choice(LEGIT_REQ),
        "benefits": random.choice(LEGIT_BEN),
        "fraudulent": 0,
    }


def fake_row():
    return {
        "title": random.choice(FAKE_TITLES),
        "company_profile": random.choice(FAKE_PROFILE),
        "description": random.choice(FAKE_DESC),
        "requirements": random.choice(FAKE_REQ),
        "benefits": random.choice(FAKE_BEN),
        "fraudulent": 1,
    }


def add_noise(row):
    """Real life is messy: some legit posts say 'urgent', some scams look polished.
    Mixing sentences makes the toy dataset less trivially separable."""
    if row["fraudulent"] == 0 and random.random() < 0.15:
        row["description"] += " We have an urgent requirement and want to fill this role quickly."
    if row["fraudulent"] == 1 and random.random() < 0.25:
        row["description"] += " " + random.choice(LEGIT_DESC)
        row["requirements"] = random.choice(LEGIT_REQ)
    return row


def main(n_legit=1700, n_fake=300):
    rows = [add_noise(legit_row()) for _ in range(n_legit)] + [add_noise(fake_row()) for _ in range(n_fake)]
    df = pd.DataFrame(rows).sample(frac=1, random_state=1).reset_index(drop=True)
    out = Path(__file__).resolve().parent.parent / "data" / "jobs.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows to {out}  (fake share: {df.fraudulent.mean():.1%})")


if __name__ == "__main__":
    main()
