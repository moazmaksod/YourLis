-- Create the SendOutLog table if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[SendOutLog]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[SendOutLog](
        [LogID] [int] IDENTITY(1,1) NOT NULL,
        [PatientID] [nvarchar](50) NOT NULL,
        [TestName] [nvarchar](100) NOT NULL,
        [SentDate] [datetime] NULL,
        CONSTRAINT [PK_SendOutLog] PRIMARY KEY CLUSTERED ([LogID] ASC)
    );
END
GO

-- Insert all existing sent samples using their request date
INSERT INTO dbo.SendOutLog (PatientID, TestName, SentDate)
SELECT 
    pt.patientid, 
    pt.testsimp, 
    pt.requestdate
FROM 
    dbo.patienttest pt
LEFT JOIN 
    dbo.SendOutLog sol ON pt.patientid = sol.PatientID AND pt.testsimp = sol.TestName
WHERE 
    pt.sentout = 1 
    AND pt.send = 1
    AND sol.LogID IS NULL
    AND EXISTS (SELECT 1 FROM dbo.payment pay WHERE pay.patientid = pt.patientid AND pay.testsimp = pt.testsimp);
GO