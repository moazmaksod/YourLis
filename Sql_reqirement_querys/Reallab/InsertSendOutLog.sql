
-- Drop the procedure if it already exists
IF OBJECT_ID('dbo.InsertSendOutLog', 'P') IS NOT NULL
    DROP PROCEDURE dbo.InsertSendOutLog;
GO

-- Create the stored procedure for inserting a send-out log entry
CREATE PROCEDURE dbo.InsertSendOutLog
    @PatientID NVARCHAR(50),
    @TestName NVARCHAR(100),
    @SentDate DATETIME
AS
BEGIN
    SET NOCOUNT ON;

    -- Check if a record for this patient and test already exists
    IF NOT EXISTS (SELECT 1 FROM dbo.SendOutLog WHERE PatientID = @PatientID AND TestName = @TestName)
    BEGIN
        -- Insert a new log entry
        INSERT INTO dbo.SendOutLog (PatientID, TestName, SentDate)
        VALUES (@PatientID, @TestName, @SentDate);
    END
    -- If it exists, we do nothing to prevent duplicate entries.
    -- Alternatively, we could update the SentDate, but for logging, insertion is often better.
END
GO
