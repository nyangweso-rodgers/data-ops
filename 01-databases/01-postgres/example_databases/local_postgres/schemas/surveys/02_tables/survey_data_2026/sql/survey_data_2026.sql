with
survey_data_2026_cte as (
	SELECT id, start_time, completion_time, email, 
	"name", 
	data_consent, 
	branch_attended, participant_type, phone, recommend_score, heard_about_show, improvements_noticed, change_or_improve, 
	return_next_year, age_range, years_attended, visiting_with, rating_venue_layout, rating_signage, rating_parking, rating_cleanliness, rating_restrooms, rating_security, 
	rating_exhibitions, rating_entertainment, rating_entry_fee_value, rating_overall_organization, time_spent, made_purchases, attracted_by, organization, "role", years_exhibiting, industry, rating_registration, rating_booth_location, rating_booth_size, rating_event_logistics, rating_foot_traffic, rating_visitor_interactions, rating_roi, rating_staff_support, _sync_at
	FROM surveys.survey_data_2026
	),
agg_survey_data_2026_cte as (
	select distinct 
	branch_attended,
	count(*) as record_count
	from survey_data_2026_cte
	group by 1
	order by 2 desc
	)
select *
--from survey_data_2026
from agg_survey_data_2026_cte
limit 1000