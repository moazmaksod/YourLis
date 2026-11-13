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

    -- Check if the test is a valid send-out test
    IF EXISTS (SELECT 1 FROM dbo.patienttest WHERE patientid = @PatientID AND testsimp = @TestName AND sentout = 1)
    BEGIN
        -- Use SendOutLog table to track sent status and date instead of updating patienttest
        IF EXISTS (SELECT 1 FROM dbo.SendOutLog WHERE PatientID = @PatientID AND TestName = @TestName)
        BEGIN
            UPDATE dbo.SendOutLog
            SET SentDate = @SentDate
            WHERE PatientID = @PatientID AND TestName = @TestName;
        END
        ELSE
        BEGIN
            INSERT INTO dbo.SendOutLog (PatientID, TestName, SentDate)
            VALUES (@PatientID, @TestName, @SentDate);
        END
    END
END
GO
