okay, so i cleaned up the repository so things are more streamlined now. i need the consensus analyzer to be such that if it runs (assume first round w/ its threshold) and there are questions that arent at the threshold

when first running the consensus_analyzer, it should create a folder with the consensus_report. the first report will be called consensus_report_vote_01_{time}.

first, find the questions of the latest consensus_report that fail the threshold.



the ai should only have to go through the question banks which they couldn't solve. they should also be provided with the answers and 

the consensus_report_ files are to always include all questions. but they should update with the addition of consensus_report_vote_XX_{time}


consensus_report_final.json should be the report which is read by the consensus_validation in the next step. update consensus_validation to solely read this file.


the consensus_validation should take into account the vote_01 solely for the model success/failures, and a metric for if the model corrects itself best when there is consensus.