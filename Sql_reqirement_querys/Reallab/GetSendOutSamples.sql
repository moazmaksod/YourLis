-- Drop the procedure if it already exists to ensure a clean update
IF OBJECT_ID('dbo.GetSendOutSamples', 'P') IS NOT NULL
    DROP PROCEDURE dbo.GetSendOutSamples;
GO

-- Create the stored procedure for searching send-out samples
CREATE PROCEDURE dbo.GetSendOutSamples
    @PatientID NVARCHAR(50) = NULL,
    @PatientName NVARCHAR(100) = NULL,
    @StartDate DATE = NULL,
    @EndDate DATE = NULL,
    @DestinationLab NVARCHAR(100) = NULL,
    @Status NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    -- This query joins patienttest, patientinfo, and the new SendOutLog table.
    SELECT
        pt.patientid AS [Patient ID],
        p.patientnamear AS [Name],
        pt.testsimp AS [Test Name],
        pt.otherlabname AS [Destination Lab],
        pt.testpriceout AS [Price],
        pt.testpriceoutmadfo AS [Amount Paid],
        sol.SentDate AS [Sent Date], -- Get Sent Date from SendOutLog
        CASE 
            WHEN sol.SentDate IS NOT NULL THEN 'Sent'
            ELSE 'Pending'
        END AS [Status]
    FROM
        dbo.patienttest pt
    LEFT JOIN
        dbo.patientinfo p ON pt.patientid = p.patientid
    LEFT JOIN
        dbo.SendOutLog sol ON pt.patientid = sol.PatientID AND pt.testsimp = sol.TestName
    WHERE
        pt.sentout = 1  -- Filter for only tests intended to be sent out
        AND (@PatientID IS NULL OR pt.patientid LIKE '%' + @PatientID + '%')
        AND (@PatientName IS NULL OR p.patientnamear LIKE '%' + @PatientName + '%')
        AND (@StartDate IS NULL OR CONVERT(date, pt.requestdate) >= @StartDate)
        AND (@EndDate IS NULL OR CONVERT(date, pt.requestdate) <= @EndDate)
        AND (@DestinationLab IS NULL OR pt.otherlabname LIKE '%' + @DestinationLab + '%')
        AND (@Status IS NULL OR 
            (@Status = 'Sent' AND sol.SentDate IS NOT NULL) OR 
            (@Status = 'Pending' AND sol.SentDate IS NULL)
        )
    ORDER BY
        pt.requestdate DESC;
END
GO
