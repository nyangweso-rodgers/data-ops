with
survey_data_2025_cte as (
	SELECT id, start_time, completion_time, email, name, "language", privacy_policy, 
	participant_type, branch_attended, organization, industry, heard_about_show, experience_level, interests, recommend_score, keep_doing, change_or_improve, 
	first_name, last_name, phone_number, email_address, job_title, city, gender, age_range, primary_activity, 
	_sync_at
	FROM surveys.survey_data_2025
	),
agg_survey_data_2025_cte as (
	select distinct branch_attended,
	participant_type,
	count(*) as record_count,
	max(_sync_at) as max_sync_at
	from survey_data_2025_cte
	group by 1,2
	order by 1,2
	)
select *
from agg_survey_data_2025_cte
limit 1000