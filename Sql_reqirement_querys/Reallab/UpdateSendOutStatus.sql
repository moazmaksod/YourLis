-- Drop the procedure if it already exists to ensure a clean update
IF OBJECT_ID('dbo.UpdateSendOutStatus', 'P') IS NOT NULL
    DROP PROCEDURE dbo.UpdateSendOutStatus;
GO

-- Create the stored procedure to update a sample's status to 'Sent'
CREATE PROCEDURE dbo.UpdateSendOutStatus
    @PatientID NVARCHAR(50),
    @TestName NVARCHAR(100),
    @SentDate DATETIME
AS
BEGIN
    SET NOCOUNT ON;

    -- Update the 'send' status to 'Sent' and set the 'taslimdate'
    -- This identifies the specific test for the patient to update.
    UPDATE dbo.patienttest
    SET
        send = 1,
        taslimdate = @SentDate
    WHERE
        patientid = @PatientID
        AND testsimp = @TestName
        AND sentout = 1;
END
GO
