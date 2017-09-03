(--start a local scope. You can add a MacroScript definition above to make it a button
--pick the file:
local theFilename = getOpenFileName types:"Comma Separated Values (*.CSV)|*.CSV|All Files (*.*)|*.*"
if theFilename != undefined do ( --if a valid filename picked,
    local theFile = openFile theFilename --open the file
    local theDummy = Point showtrajectory:true --create a helper with trajectory on
    while not eof theFile do ( --loop until the end of tile
        theTime = floor ((readValue theFile)*25 + 0.5) --read time and round to closest frame
		if theTime > 0 do(
		animationRange = interval 0 theTime
		)
        with animate on --enable autokey animation context
            at time theTime  --set the current time for the following expression
				theDummy.transform = Matrix3 [(readValue theFile),(readValue theFile),(readValue theFile)] [(readValue theFile),(readValue theFile),(readValue theFile)] [(readValue theFile),(readValue theFile),(readValue theFile)] [(readValue theFile),(readValue theFile),(readValue theFile)]			
    )--and read the position from the file for each time step
    close theFile --close the file when done
)--end if
)--end script