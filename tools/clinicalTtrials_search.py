from pytrials.client import ClinicalTrials

ct = ClinicalTrials()

# Get 50 full studies related to Coronavirus and COVID in csv format.
ct.get_full_studies(search_expr="Coronavirus+COVID", max_studies=50)

# Get the NCTId, Condition and Brief title fields from 1000 studies related to Coronavirus and Covid, in csv format.
corona_fields = ct.get_study_fields(
    search_expr="Coronavirus+COVID",
    fields=["NCT Number", "Conditions", "Study Title"],
    max_studies=1000,
    fmt="csv",
)

# Read the csv data in Pandas
import pandas as pd

df = pd.DataFrame.from_records(corona_fields[1:], columns=corona_fields[0])
print(df.head())