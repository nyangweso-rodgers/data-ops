with
survey_data_nanyuki_2025_cte as (
	SELECT id, start_time, completion_time, email, "name", "language", branch_attended, organization, company_headquarters, contact_person, job_title, phone_number, email_address, industry, familiarity_with_services, heard_about_show, received_support, generated_engagement, lead_quality, well_organized_and_promoted, participate_again, recommend_to_others, expectations, suggestions, _sync_at
	FROM surveys.survey_data_nanyuki_2025
	),
agg_survey_data_nanyuki_2025_cte as (
	select 
	count(*)
	from survey_data_nanyuki_2025_cte
	)
select *
--from survey_data_nanyuki_2025_cte 
from agg_survey_data_nanyuki_2025_cte
limit 1000